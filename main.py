#!/usr/bin/env python3

# Downloads attachments from applications listed in constants.py
# TODO: 
#   - downloading attachments can fail and retry will not catch unless cache database is removed
#   - Rerunning the process does not delete outdated attachments or mark disappeared people
#   - Excel sharing mode gets disabled during running

from timeit import repeat
import requests
from constants import *
import browser_cookie3
import code
from copy import deepcopy
import pathlib
from pathlib import Path
import logging
DEBUG = False
from pprint import pprint
output_path = Path(OUTPUT_PATH)
output_path.mkdir(exist_ok=True)
import cgi
import shelve
from concurrent import futures
import filecmp
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import threading
import queue
import hashlib
import os
import coloredlogs
# Queue for applications
applications_queue = queue.Queue(4)

retries = Retry(total=5, backoff_factor=1)


import http.client as http_client

log = logging.getLogger(__name__)
fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)

formatter = coloredlogs.ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)


logging.getLogger().addHandler(fh)

if DEBUG:
    coloredlogs.install(level='DEBUG')
else:
    coloredlogs.install(level='INFO', logger=log)


requests_log = logging.getLogger("requests.packages.urllib3")
if DEBUG:
    http_client.HTTPConnection.debuglevel = 1
    requests_log.setLevel(logging.DEBUG)
else:
    http_client.HTTPConnection.debuglevel = 0
    requests_log.setLevel(logging.ERROR)


log.info("Starting Opintoscraper")






requests_log.propagate = True

## Application database
db_downloaded = shelve.open(DATABASE_PATH)
db_applications = shelve.open(str(Path(DATABASE_PATH).with_suffix(".applications.slf")))


def application_already_downloaded(oid):
    return db_downloaded.get(oid)


def mark_as_downloaded(oid):
    db_downloaded[oid] = True


# Common session used to store cookies, also with retry
session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


def rebuild_cookies():
    """ Steal browser cookies again """
    log.info("rebuildCookies()")
    cookies = browser_cookie3.firefox(cookie_file="/kvhaku/firefox/profile/cookies.sqlite")  #browser_cookies = browser_cookie3.load()
    session.cookies = cookies


rebuild_cookies()


def getCSRF():
    return session.cookies._cookies[".opintopolku.fi"]["/"]["CSRF"].value


def generate_header():
    return {
        "csrf": getCSRF(),
        "origin": "https://virkailija.opintopolku.fi",
        "accept": "application/json",
        "caller-id": "requestscraper-utu-tech-lamkoiatutufi"
    }


def check_is_logged_in():
    # Test if logged in
    try:
        infotest = session.get(ME2_INFO_URL,allow_redirects=False)
    except:
        return False
    return infotest.status_code == 200


while not check_is_logged_in():
    log.error("Could not login to https://virkailija.opintopolku.fi/ ")
    input(
        "Could not login to https://virkailija.opintopolku.fi/ . Try logging in with a browser (microsoft edge) and press enter."
    )
    rebuild_cookies()

import time
bad_login = threading.Event()
good_login = threading.Event()
good_login.set()


def invalidate_login_wait_for_login():
    log.warning("[Worker] Detected a likely login failure, waiting for login")
    if not bad_login.is_set():
        good_login.clear()
        bad_login.set()
    good_login.wait()
    log.warning("resuming after good login...")


def download_file_to(file_guid, target_folder):
    good_login.wait()
    assert isinstance(file_guid, str)
    url = FILE_DOWNLOAD_URL.format(file_guid=file_guid)

    #oid=application["person"]["oid"]
    attachment_file = session.get(url, headers=generate_header())
    if attachment_file.status_code == 401:
        invalidate_login_wait_for_login()
        attachment_file = session.get(url, headers=generate_header())
    elif attachment_file.status_code == 404:
        if not check_is_logged_in():
            invalidate_login_wait_for_login()
            attachment_file = session.get(url, headers=generate_header())
        return (file_guid, False)
    assert attachment_file.status_code == 200
    filename = cgi.parse_header(
        attachment_file.headers["Content-Disposition"])[1]["filename"]
    path = (target_folder / filename)
    opath = path

    # Check existing and create if not
    exists = None
    try:
        with path.open("xb") as f:
            exists = False
    except FileExistsError as e:
        exists = True

    if exists:
        for i in range(99999):
            path = opath.with_stem(opath.stem + "_n" + str(i))

            # avoid race condition by create-opening exclusively (error if already existing)
            try:
                with path.open("xb") as f:
                    break
            except FileExistsError as e:
                continue

    sha1 = hashlib.sha1()
        
    with path.open("wb") as f:
        for chunk in attachment_file.iter_content(chunk_size=8192):
            f.write(chunk)
            sha1.update(chunk) 

    # TODO: Non-fatal race condition (dedupe.py takes care of)
    if path != opath and filecmp.cmp(path, opath):
        path.unlink()
        log.warning("\t %s is dupe of %s (removing)",str(path),str(opath))
        path = opath
        #TODO: compare all "revision"

    return (file_guid, path,sha1.digest())


oid_processed = {}


def on_cookies_stale():
    log.error("Likely logged out. Press enter to continue after logging in.")
    input("Likely logged out. Press enter to continue after logging in.")
    rebuild_cookies()
    log.info("Rebuilt cookies...")


def push_application_queue(payload):
    while True:
        if bad_login.is_set():
            log.warning("Got bad login flag, checking")
            if check_is_logged_in():
                log.info("We are logged in, clearing")
                bad_login.clear()
                good_login.set()
            else:
                on_cookies_stale()
        try:
            applications_queue.put(payload, True, 5)
            break
        except queue.Full as e:
            if not check_is_logged_in():
                on_cookies_stale()


def process_application(application,oidshort):

    person_oid=application["person"]["oid"]
    application_oid = application["key"]


    last_name =application["person"]["last-name"]
    preferred_name = application["person"]["preferred-name"]
    try:
        person_path=next(Path(output_path).glob(f'*_{person_oid}'))
        folder_name=os.path.basename(os.path.normpath(person_path))
        #log.info(f'Using existing path, {person_path} for {last_name}, {application["person"]["preferred-name"]}')
    except StopIteration:
        folder_name = "{0}_{1}_{2}".format(last_name,
                                       preferred_name.replace("/","_"),
                                       person_oid)
        person_path = output_path / folder_name
        log.info(f'Using new path, {person_path} for {person_oid}')


    if not DISABLE_EXCEL:
        excel.set_applicant(application_oid,preferred_name,last_name,str(folder_name),oidshort)

    if oid_processed.get(application_oid):
        log.debug("Already processed %s (this session)",application_oid)
        return

    oid_processed[application_oid] = True
    application["folder"]=str(person_path)
    db_applications[application_oid]=application
    # UNDONE: DANGEROUS: Would not download attachments for people with multiple applications
    #if person_path.exists():
    if (not DISABLE_EXCEL and EXCEL_ONLY) or DB_ONLY:
        return

    if application_already_downloaded(application_oid):
        log.info("Already processed: %s", folder_name)
        return
    else:
        log.debug("Queued: %s", folder_name)
    person_path.mkdir(exist_ok=True)

    target_path = (person_path)
    Path(target_path).mkdir(exist_ok=True, parents=True)

    # details not in list, such as attachment info
    url = APPLICATION_URL.format(oid=application_oid)
    application_details = session.get(url, headers=generate_header())

    if application_details.status_code == 401:
        input("relogin and press enter")
        rebuild_cookies()
        application_details = session.get(url, headers=generate_header())

    assert application_details.status_code == 200
    application_details = application_details.json()
    data = (application_oid, application_details, target_path, person_path)
    push_application_queue(data)

import excel

# Downloading applications takes a while so use a queue
def process_application_postprocess(data):
    application_oid, application_details, target_path, person_path = data
    log.debug("Postprocessing %s", person_path)
    filtered_attachments = []
    for oid, val in application_details['attachment-reviews'].items():
        if oid in TARGET_OIDS:
            filtered_attachments += list(val.keys())
    no_failed_downloads = True
    for answer in application_details["application"]["answers"]:
        if answer["fieldType"] != "attachment":
            continue
        key = answer["key"]
        if key not in filtered_attachments:
            log.info("\t filtered %s for %s (not needed)",key,person_path)
            continue
        values = answer["value"]
        # sometimes it's a list of strings, sometimes a list of lists
        downloadables = []
        for attachment_file_guids in values or []:

            # sometimes it's a list, sometimes a string (but why?)
            if isinstance(attachment_file_guids, str):
                attachment_file_guids = [attachment_file_guids]
            for attachment_file_guid in attachment_file_guids or []:

                downloadables.append(attachment_file_guid)

        # Remove potential duplicates
        olen = len(downloadables)
        downloadables = sorted((set(downloadables)))
        nlen = len(downloadables)
        if olen != nlen:
            log.info("\tReduced downloadables %s -> %s",olen,nlen)
        with futures.ThreadPoolExecutor(max_workers=5) as executor:
            res = executor.map(lambda x: download_file_to(x, target_path),
                               downloadables)
            for (guid, filepath, checksum) in res:
                if not filepath:
                    no_failed_downloads = False
                    log.warning("\tCould not download %s", guid)
                else:
                    log.info("\tDownloaded %s", filepath)
    if no_failed_downloads:
        mark_as_downloaded(application_oid)
    else:
        log.error("Unable to complete %s", application_oid)


def application_processor_thread():
    while True:
        data = applications_queue.get()
        if data == False:
            break
        process_application_postprocess(data)


app_proc = threading.Thread(target=application_processor_thread, daemon=True)
app_proc.start()

# Iterate over application targets (?)
for oid, oid_folder_name in TARGET_OIDS.items():
    log.info("-")
    log.info("Requesting %s", oid_folder_name)
    
    query = deepcopy(LIST_URL_QUERY)
    query["hakukohde-oid"] = oid
    offset=None

    for i in range(1,10):
        assert i<5,"pagination fail"

        if offset:
            query["sort"]["offset"]=offset

        applications_list = session.post(LIST_URL,
                                     json=query,
                                     headers=generate_header())
        if applications_list.status_code == 401:
            raise Exception("likely not logged in")
        assert applications_list.status_code == 200

        applications_list = applications_list.json()

        #assert not applications_list["sort"].get("offset"), "???"
        offset=applications_list["sort"].get("offset")

        logging.info("application count for %s: %d (page %d)", oid_folder_name,
            len(applications_list["applications"]),i)
        for application in applications_list["applications"]:
            #pass
            process_application(application,oid_folder_name)

        if not offset:
            break
        else:
            log.warning("Using experimental pagination for %s",str(oid_folder_name))


excel.save()
applications_queue.put(False)
log.info("Waiting for finishing...")
app_proc.join()
log.warning("Processing finished!")