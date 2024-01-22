#!/usr/bin/env python3
#
# Processes every application from application cache database with chrome, producing a pdf with person-oid's application
#
# # TODO
#
# - !!! SINGLE APPLICATION, MULTIPLE PERSONS
#    - should treat as separate people?
#
#
import os
os.environ["MOZ_HEADLESS"]='1'
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time,base64
import constants
from pathlib import Path
import coloredlogs,logging
import fcntl
import portalocker
import re,shelve
from systemd.journal import JournalHandler
OUT_FILE="_virkailija_tulostus.pdf"
PARALLEL_COUNT=1

import threading
import queue
applications_queue = queue.Queue(14)


log = logging.getLogger(__name__)
def init_logging():
    #fh = logging.FileHandler('debug_browser.log')
    fh=JournalHandler()

    fh.setLevel(logging.DEBUG)

    #formatter = coloredlogs.ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = coloredlogs.ColoredFormatter('%(name)s - %(levelname)s - %(message)s - [%(threadName)s]')
    fh.setFormatter(formatter)
    coloredlogs.DEFAULT_FORMAT_STYLE

    logging.getLogger().addHandler(fh)

    with_thread_formatter = coloredlogs.ColoredFormatter('%(asctime)s %(hostname)s %(name)s[%(process)d][%(threadName)s] %(levelname)s %(message)s')
    coloredlogs.install(level='INFO', logger=log,formatter=with_thread_formatter)
init_logging()

log.info("Browser logger")

db_applications = shelve.open(str(Path(constants.DATABASE_PATH).with_suffix(".applications.slf")),flag='r', writeback=False)
targets={}
for app_oid,app_info in db_applications.items():
    path = Path(app_info["folder"])
    if not path.exists():
        log.error("does not exist?? %s",str(path))
        continue
    name=path.name
    targets[app_oid]=path

log.info("Application count: %s",len(targets))

def process_thread():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-extensions")
    #options.add_argument("--user-data-dir=/tmp/chromesel")

    #options.set_preference('profile', "/kvhaku/firefox/profile/")

    driver = webdriver.Chrome(options=options)

    #driver.get("https://virkailija.opintopolku.fi/henkilo-ui/omattiedot")
    import browser_cookie3
    cookie_jar = browser_cookie3.firefox(cookie_file="/kvhaku/firefox/profile/cookies.sqlite")


    driver.get("https://virkailija.opintopolku.fi")

    for cookie in cookie_jar:
        cookie_dict = {"domain": cookie.domain, "name": cookie.name, "value": cookie.value, "secure": True if cookie.secure else False}
        if cookie.expires:
            cookie_dict["expiry"] = cookie.expires
        if cookie.path_specified:
            cookie_dict["path"] = cookie.path
        if not cookie.domain or cookie.domain.find("opintopolku.fi")!=-1:
            driver.add_cookie(cookie_dict)

    print_options = PrintOptions()
    #print_options.page_height = 8.5
    #print_options.page_width = 11
    #print_options.scale = 0.3


    def saveApplicant(oid,filepath):

        #except portalocker.exceptions.LockException as e:

        with portalocker.Lock(filepath,mode='ab',fail_when_locked=True) as pdf_fd:

            driver.get("https://virkailija.opintopolku.fi/lomake-editori/applications/search?term="+str(oid))

            try:
                elem=WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".application-handling__list-row--application-applicant")))
                if len(driver.find_elements(By.CLASS_NAME,'application-handling__list-row--application-applicant'))>1:
                    log.warning("More than one application for %s, skipping guessing!",filepath)
                    return False
                    #elem.click()

            except TimeoutException as e:
                print(driver.page_source)
                print("@",driver.current_url)
                driver.get_screenshot_as_file('test.png')


                log.error("Unknown error or no applications for %s: %s",oid,str(e))
                return False

            required_class="application-handling__review-area-haku-heading"
            for _ in range(2):
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, required_class)))
                except TimeoutException as e:
                    log.error("Application element missing for %s: %s",oid,str(e))
                    return False

                opening_new_application=False
                for _ in range(5):

                    try:
                        WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a#notification-link-form-outdated"))).click()
                        log.info("Switching to newer form version for %s",oid)
                        time.sleep(5)
                        opening_new_application=True
                        break
                    except TimeoutException as e:
                        opening_new_application=True
                        break
                    except StaleElementReferenceException as e:
                        log.warning("Stale oops on click attempt %s",oid)
                        time.sleep(5)
                        continue

                if not opening_new_application:
                    break

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, required_class)))
            except TimeoutException as e:
                log.error("Application element missing (2) for %s: %s",oid,str(e))
                return False

            data=base64.b64decode(driver.print_page(print_options))
            if len(data)<1024*5:
                log.error("Invalid filesize for %s, not saving",filepath)
                return False

            pdf_fd.write(data)
            log.debug("Saving %s",filepath)
    try:
        log.info("Worker ready")
        while True:
            task=applications_queue.get()
            if task==False:
                break
            app,filepath = task
            log.info("Processing %s",filepath)
            saveApplicant(app,filepath)
        log.info("Worker has been requested to close!")
    finally:
        log.info("quitting worker")
        try:
            driver.quit()
        except Exception as e:
            log.critical(str(e))

#TODO: better way to sync multiple workers?
import random
items=targets.items() # List of tuples

threads=[]
for i in range(PARALLEL_COUNT):

    worker = threading.Thread(target=process_thread, daemon=True,name="Application Worker Process "+str(i))
    worker.start()

    threads.append(worker)

for oid,path in targets.items():
    filepath=path/OUT_FILE
    if not filepath.exists() or filepath.stat().st_size<1024*20 or filepath.stat().st_mtime<1674737600:
        try:
            applications_queue.put((oid,filepath))
        except portalocker.exceptions.AlreadyLocked as ioe:
            log.warning("Skipping %s, locked.",filepath)
    else:
        pass
        log.debug("Skipping %s, already exists",filepath)


log.info("Waiting for workers to finish...")
for thread in threads:
    applications_queue.put(False)

for thread in threads:
    thread.join()

assert applications_queue.empty()

""""
#print(driver.page_source)
print("@",driver.current_url)

for request in driver.requests:
    if request.response and request.response.status_code!=200:
        print(
            request.url,
            request.response.status_code,
            request.response.headers['Content-Type']
        )

print(driver.page_source)
print("@",driver.current_url)
driver.get_screenshot_as_file('test.png')
"""

