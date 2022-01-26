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

db = shelve.open('database')


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


def downloadFileTo(file_guid, target_folder):
    assert isinstance(file_guid, str)
    url = FILE_DOWNLOAD_URL.format(file_guid=file_guid)

    #oid=application["person"]["oid"]
    attachment_file = session.get(url, headers=generateHeader())
    if attachment_file.status_code == 401:
        input("relogin and press enter")
        rebuildCookies()
        attachment_file = session.get(url, headers=generateHeader())
    elif attachment_file.status_code == 404:
        if not testLoggedIn():
            input("relogin and press enter")
            rebuildCookies()
            attachment_file = session.get(url, headers=generateHeader())

    assert attachment_file.status_code == 200
    filename = cgi.parse_header(
        attachment_file.headers["Content-Disposition"])[1]["filename"]
    path = (target_folder / filename)
    opath=path
    if path.exists():
        for i in range(99999):
            path = opath.with_stem(opath.stem + "_n" + str(i))
            if not path.exists():
                break

    with path.open("wb") as f:
        for chunk in attachment_file.iter_content(chunk_size=8192):
            f.write(chunk)
    if path!=opath and filecmp.cmp(path,opath):
        path.unlink()
        print("\t\t","^ is dupe to",opath,"removing")
        path=opath
        #TODO: compare all "revision"

    return path


oid_processed = {}


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
        print("\nAlready processed", folder_name)
        return
    else:
        print("\nProcessing", folder_name)
    person_path.mkdir(exist_ok=True)

    #with (person_path/"info.txt").open("w") as f:
    #    f.write(application["person"]["last-name"])
    #    f.write("\n")
    #    f.write(application["person"]["preferred-name"])

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
    filtered_attachments = []
    for oid, val in application_details['attachment-reviews'].items():
        if oid in TARGET_OIDS:
            filtered_attachments += list(val.keys())

    for answer in application_details["application"]["answers"]:
        if answer["fieldType"] != "attachment":
            continue
        key = answer["key"]
        if key not in filtered_attachments:
            print("\t", "filtered", key, "for", person_path)
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

        with futures.ThreadPoolExecutor(max_workers=5) as executor:
            res = executor.map(lambda x: downloadFileTo(x, target_path),
                               downloadables)
            for r in res:
                print("\tDownloaded", r)
    markAsDownloaded(application_oid)


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

print("Processing finished!")