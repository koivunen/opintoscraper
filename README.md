# opintoscraper

A web scraper for application attachments from https://virkailija.opintopolku.fi/lomake-editori/ for mass processing of up to thousands of applications/applicants. This process is not officially supported and may break at any moment, you have been warned.

### Documentation is out of date!

2023 update brings excel sheet generation and scraping applicant form to PDF with the usual attachments (WIP)

### Requirements

 - Linux server (with disk encryption) `/kvhaku`
 - https://github.com/jlesage/docker-firefox (for login cookies until proper login API is used)
 - Python 3.11+
 - Programming experience (for now)
 - chromium with selenium (headless)
   - Min 32GB RAM for 5 parallel printing jobs (memory leak?) 

### Usage

 - Install dependencies from requirements.txt (`pip install -r requirements.txt`)
 - Set up target program IDs in `constants.py` (program groups are not supported yet!) as seen in opintopolku.
 - Login to [https://virkailija.opintopolku.fi/](https://virkailija.opintopolku.fi/) using Firefox to steal cookies (TODO use real API)  
```bash
docker run -e VNC_PASSWORD=PASSWORDHERE -e SECURE_CONNECTION=1  --name=firefox     -p 5800:5800 -e 'FF_OPEN_URL=https://virkailija.opintopolku.fi/service-provider-app/saml/login/alias/hakasp?redirect=https://virkailija.opintopolku.fi/virkailijan-tyopoyta/authenticate'     -v /kvhaku/firefox:/config:rw     jlesage/firefox
```

 - Run `main.py` and watch for the process to fail or finish. 
    - You may be logged out of opintopolku in the middle in which case you need to login back with edge and press enter. The program will prompt you for this.
   - On failure: you may need to rerun the program in which case it skips every application already dowloaded based on the `database` cache file next to main.py
 - After mass download, run `dedupe.py` to remove duplicate application files with different filenames  (TODO: no longer required?)
 - Rename/remove `database*` files to reinitialize the downloader!
   - The database stores application ids that have already been processed

### Default output format description

  - The attachments will be saved into `output` folder with original filenames.
     - Duplicate names are prefixed with _n0 _n1 and so forth
  - The folder format is `last name_Preferred first_personOID` so for example `meikäläinen_matti_1.2.3.123124345235235`.
     - NOTE: A person may have multiple applications with different names so there may exist for example.
     - IN ADDITION: Multiple applications with attachments may get merged to the same folder

### TODO / issues / Help wanted

 - (G)UI for setting up
 - Use official API
 - no easy way to use/configure 
 - Does not use official APIs.
 - not configurable output target format (for example per-program folder for attachments)
 - Parallel application fetching (instead of just downloading) for a speedup of about 1 hour for 1000 applications (currently takes about 5 hours)
 - Proper logging
 - Download only changed since X (and list changed folders)
 - `export DBUS_SESSION_BUS_ADDRESS=/dev/null ./browser.py`
 - Allow marking in excel as rejected and remove attachments folder accordingly
 - deduping applications support
 - excel shared workbook

## SECURITY

 - Known PII leak targets: /tmp contains chrome profiles, chrome log files may be elsewhere, cache contains applications
 - Always encrypt the cache and preferably the whole opintoscraper, for example:  
```bash
 cryptsetup luksFormat /dev/nvme1n1p3
 cryptsetup luksOpen /dev/nvme1n1p3 opintoscraper
 mkfs.ext4 -L opintoscraperdata /dev/mapper/opintoscraper
 mount /dev/mapper/opintoscraper /kvhaku/
```
 - Always run in a secure environment altogether!
 - Target folders for downloads should be restricted from people as much as possible and after selection process the files should be archived in a inaccssible place

## Misc
- Likely the correct documentation for the API: https://wiki.eduuni.fi/display/ophpolku/Hakemuspalvelun+Siirto-API
- The internal API used by us is likely the same; the only differences seem to be in authentication


Also worth checking: https://wiki.eduuni.fi/display/ophpolku/Hakeneet+ja+paikan+vastaanottaneet+%28kk%29+v4

We are likely interfacing with the api that https://github.com/Opetushallitus/ataru creates/uses.

Also check (api complains if you don't give caller-id):
https://github.com/Opetushallitus/dokumentaatio/blob/master/http.md

Misc links:

https://wiki.eduuni.fi/display/ophoppija/Hakemuspalvelun+REST+API

https://virkailija.opintopolku.fi/suoritusrekisteri/swagger/index.html#/kkhakijat/haeKkHakijat

https://opintopolku.fi/konfo-backend/swagger/index.html

https://wiki.eduuni.fi/display/ophpolku/Hakeneet+ja+paikan+vastaanottaneet+%28kk%29+v4

