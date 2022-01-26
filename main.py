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
applications_queue = queue.Queue(4)
retries = Retry(total=5, backoff_factor=1)

import http.client as http_client
if DEBUG:
    http_client.HTTPConnection.debuglevel = 1

logging.basicConfig()
if DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
if DEBUG:
    requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

## Application database

db = shelve.open(DATABASE_PATH)


def hasDownloadedApplication(oid):
    return db.get(oid)


def markAsDownloaded(oid):
    db[oid] = True


# Common session used to store cookies, also with retry
session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


def rebuildCookies():
    cookies = browser_cookie3.edge()  #browser_cookies = browser_cookie3.load()
    session.cookies = cookies


rebuildCookies()


def getCSRF():
    return session.cookies._cookies[".opintopolku.fi"]["/"]["CSRF"].value


def generateHeader():
    return {
        "csrf": getCSRF(),
        "origin": "https://virkailija.opintopolku.fi",
        "accept": "application/json",
        "caller-id": "requestscraper-utu-tech-lamkoiatutufi"
    }


def testLoggedIn():
    # Test if logged in
    try:
        infotest = session.get(ME2_INFO_URL)
    except:
        return False
    return infotest.status_code == 200


while not testLoggedIn():
    input(
        "Could not login to https://virkailija.opintopolku.fi/ . Try logging in with a browser (microsoft edge) and press enter."
    )
    rebuildCookies()

import time
bad_login = threading.Event()
good_login = threading.Event()
good_login.set()


def doBadLoginAndWaitForGood():
    print("[Worker] Detected a likely login failure, waiting for login")
    if not bad_login.is_set():
        good_login.clear()
        bad_login.set()
    good_login.wait()
    print("resuming after good login...")


def downloadFileTo(file_guid, target_folder):
    good_login.wait()
    assert isinstance(file_guid, str)
    url = FILE_DOWNLOAD_URL.format(file_guid=file_guid)

    #oid=application["person"]["oid"]
    attachment_file = session.get(url, headers=generateHeader())
    if attachment_file.status_code == 401:
        doBadLoginAndWaitForGood()
        attachment_file = session.get(url, headers=generateHeader())
    elif attachment_file.status_code == 404:
        if not testLoggedIn():
            doBadLoginAndWaitForGood()
            attachment_file = session.get(url, headers=generateHeader())
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
        print("\t", path, "is dupe of", opath, " (removing)")
        path = opath
        #TODO: compare all "revision"

    return (file_guid, path,sha1.digest())


oid_processed = {}


def askRebuild():
    input("Likely logged out. Press enter to continue after logging in.")
    rebuildCookies()
    print("Rebuilt cookies...")


def pushApplicationQueueData(payload):
    while True:
        if bad_login.is_set():
            print("Got bad login flag, checking")
            if testLoggedIn():
                print("We are logged in, clearing")
                bad_login.clear()
                good_login.set()
            else:
                askRebuild()
        try:
            applications_queue.put(payload, True, 5)
            break
        except queue.Full as e:
            if not testLoggedIn():
                askRebuild()


def processApplication(application):

    #oid=application["person"]["oid"]
    oid = application["key"]
    application_oid = oid
    if oid_processed.get(oid):
        print("Already processed", oid, "(this session)")
        return

    oid_processed[oid] = True

    folder_name = "{0}_{1}_{2}".format(application["person"]["last-name"],
                                       application["person"]["preferred-name"],
                                       application["person"]["oid"])
    person_path = output_path / folder_name

    # UNDONE: DANGEROUS: Would not download attachments for people with multiple applications
    #if person_path.exists():

    if hasDownloadedApplication(oid):
        print("Already processed", folder_name)
        return
    else:
        print("Queued", folder_name)
    person_path.mkdir(exist_ok=True)

    target_path = (person_path)
    Path(target_path).mkdir(exist_ok=True, parents=True)

    # details not in list, such as attachment info
    url = APPLICATION_URL.format(oid=oid)
    application_details = session.get(url, headers=generateHeader())

    if application_details.status_code == 401:
        input("relogin and press enter")
        rebuildCookies()
        application_details = session.get(url, headers=generateHeader())

    assert application_details.status_code == 200
    application_details = application_details.json()
    data = (application_oid, application_details, target_path, person_path)
    pushApplicationQueueData(data)


# Downloading applications takes a while so use a queue
def processApplicationPost(data):
    application_oid, application_details, target_path, person_path = data
    print("Processing", person_path)
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
            print("\t", "filtered", key, "for", person_path, "(not needed)")
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
            print("Reduced downloadables", olen, "->", nlen)
        with futures.ThreadPoolExecutor(max_workers=5) as executor:
            res = executor.map(lambda x: downloadFileTo(x, target_path),
                               downloadables)
            for (guid, filepath, checksum) in res:
                if not filepath:
                    no_failed_downloads = False
                    print("\tCould not download", guid)
                else:
                    print("\tDownloaded", filepath)
    if no_failed_downloads:
        markAsDownloaded(application_oid)
    else:
        print("Unable to complete", application_oid)


def applicationProcessor():
    while True:
        data = applications_queue.get()
        if data == False:
            break
        processApplicationPost(data)


app_proc = threading.Thread(target=applicationProcessor, daemon=True).start()

# Iterate over application targets (?)
for oid, oid_folder_name in TARGET_OIDS.items():
    print("\nRequesting", oid_folder_name)
    query = deepcopy(LIST_URL_QUERY)
    query["hakukohde-oid"] = oid

    applications_list = session.post(LIST_URL,
                                     json=query,
                                     headers=generateHeader())

    assert applications_list.status_code == 200

    applications_list = applications_list.json()

    assert not applications_list["sort"].get("offset"), "???"
    print("application count for", oid_folder_name,
          len(applications_list["applications"]))
    for application in applications_list["applications"]:
        processApplication(application)

applications_queue.put(False)
print("Waiting for finishing...")
app_proc.join()

print("Processing finished!")