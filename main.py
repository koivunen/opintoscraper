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
db=shelve.open('database')

# Folder path plan:
# output/matti_meikalainen/kokkikoulu/hygienia.pdf
# output/matti_meikalainen/kokkikoulu/passi.pdf
# output/matti_meikalainen/koodikoulu/atkajokortti.pdf
# output/matti_meikalainen/koodikoulu/passi.pdf
# output/matti_meikalainen/oid.lnk ?

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.

import http.client as http_client
if DEBUG:
    http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
if DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
if DEBUG:
    requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

session = requests.Session()
cookies = browser_cookie3.edge()  #browser_cookies = browser_cookie3.load()
session.cookies = cookies


def getCSRF():
    return session.cookies._cookies[".opintopolku.fi"]["/"]["CSRF"].value


def generateHeader():
    return {
        "csrf": getCSRF(),
        "origin": "https://virkailija.opintopolku.fi",
        "accept": "application/json",
        "caller-id": "requestscraper-utu-tech-lamkoiatutufi"
    }


def downloadFileTo(file_guid, target_folder):
    assert isinstance(file_guid, str)
    url = FILE_DOWNLOAD_URL.format(file_guid=file_guid)
    headers = generateHeader()

    #oid=application["person"]["oid"]

    attachment_file = session.get(url, headers=headers)
    attachment_file.raise_for_status()
    assert attachment_file.status_code == 200
    filename = cgi.parse_header(
        attachment_file.headers["Content-Disposition"])[1]["filename"]
    path=(target_folder / filename)
    print(path)
    if path.exists():
        opath=path
        for i in range(99999):
            path=opath.with_stem(opath.stem+"_"+str(i))
            if not path.exists():
                break

    with path.open("wb") as f:
        for chunk in attachment_file.iter_content(chunk_size=8192):
            f.write(chunk)
    return path

oid_processed={}
def processApplication(application):
    headers = generateHeader()
    #oid=application["person"]["oid"]
    oid = application["key"]
    if oid_processed.get(oid):
        print("duplicate",oid)
        return

    oid_processed[oid]=True
    
    folder_name = "{0}_{1}_{2}".format(application["person"]["last-name"],application["person"]["preferred-name"],application["person"]["oid"])

    person_path = output_path / folder_name
    person_path.mkdir(exist_ok=True)

    #with (person_path/"info.txt").open("w") as f:
    #    f.write(application["person"]["last-name"])
    #    f.write("\n")
    #    f.write(application["person"]["preferred-name"])

    target_path = (person_path)
    Path(target_path).mkdir(exist_ok=True,parents=True)

    # details not in list, such as attachment info
    url = APPLICATION_URL.format(oid=oid)
    application_details = session.get(url, headers=headers)

    assert application_details.status_code == 200

    application_details = application_details.json()
    for answer in application_details["application"]["answers"]:
        if answer["fieldType"] != "attachment":
            continue
        key = answer["key"]

        values = answer["value"]
        # sometimes it's a list of strings, sometimes a list of lists
        for attachment_file_guids in values or []:

            # sometimes it's a list, sometimes a string (but why?)
            if isinstance(attachment_file_guids, str):
                attachment_file_guids=[attachment_file_guids]
            for attachment_file_guid in attachment_file_guids or []:

                downloadFileTo(attachment_file_guid, target_path)

# Test if logged in and get csrf
try:
    infotest = session.get(ME2_INFO_URL)
    csrf = cookies._cookies[".opintopolku.fi"]["/"]["CSRF"].value
    #print("csrf=",csrf)
    #    code.interact(local = locals())
    #print(infotest.json())
except:
    print()
    raise

# Iterate over application targets (?)
for oid, oid_folder_name in TARGET_OIDS.items():
    print("\nRequesting", oid_folder_name)
    query = deepcopy(LIST_URL_QUERY)
    query["hakukohde-oid"] = oid
    headers = generateHeader()

    applications_list = session.post(LIST_URL, json=query, headers=headers)

    assert applications_list.status_code == 200

    applications_list = applications_list.json()

    assert not applications_list["sort"].get("offset"), "???"
    print("application count for", oid_folder_name,
          len(applications_list["applications"]))
    for application in applications_list["applications"]:
        processApplication(application)
        

    