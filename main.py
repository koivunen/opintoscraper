import requests
from constants import *
import browser_cookie3
import code
from copy import deepcopy

import logging
DEBUG=False


# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
if DEBUG:
    http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
if DEBUG:
    requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


#TODO: cookie theft from chrome/electron/etc
# List->applications->attachment->file
session = requests.Session()
#browser_cookies = browser_cookie3.load()
cookies = browser_cookie3.edge()
session.cookies=cookies

# Test if logged in and get csrf
try:
    infotest=session.get(ME2_INFO_URL)
    csrf=cookies._cookies[".opintopolku.fi"]["/"]["CSRF"].value
    print("csrf=",csrf)
    print(infotest.json())
except:
    raise

# Iterate over application targets (?)
for oid,oid_folder_name in TARGET_OIDS.items():
    print("\nRequesting",oid_folder_name)
    query=deepcopy(LIST_URL_QUERY)
    query["hakukohde-oid"]=oid
    headers={
        "csrf": session.cookies._cookies[".opintopolku.fi"]["/"]["CSRF"].value,
        "origin": "https://virkailija.opintopolku.fi",
        "accept": "application/json",
        "caller-id": "1.2.246.562.10.00000000001.ataru-editori.frontend"
    }

    applications_list=session.post(LIST_URL,json=query,headers=headers)

    assert applications_list.status_code==200

    applications_list=applications_list.json()
    print(len(applications_list["applications"]))
    break