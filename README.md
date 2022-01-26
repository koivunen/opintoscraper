# opintoscraper

A web scraper for the attachments from https://virkailija.opintopolku.fi/lomake-editori/ for mass processing of up to thousands of applications. This process is not officially supported and may break at any moment, you have been warned.

### Requirements

 - Microsoft edge or a browser
 - Python 3.9
 - Programming experience (for now)

### Usage

 - Install dependencies from requirements.txt (`pip instal -r requirements.txt`)
 - Set up target program IDs in `constants.py` (program groups are not supported yet!)
 - Login to [https://virkailija.opintopolku.fi/](https://virkailija.opintopolku.fi/) in Microsoft Edge.
 - Run `main.py` and watch for the process to fail or finish. 
    - You may be logged out of opintopolku in the middle in which case you need to login back with edge and press enter. The program will prompt you for this.
   - On failure: you may need to rerun the program in which case it skips every application already dowloaded based on the `database` file next to main.py
 - After mass download, run `dedupe.py` to remove duplicate application files with different filenames and 
 - Rename/remove `database*` files to reinitialize the downloader


### Default output format description

  - The attachments will be saved into `output` folder with original filenames.
     - Duplicate names are prefixed with _n0 _n1 and so forth
  - The folder format is `last name_Preferred first_personOID` so for example `meikäläinen_matti_1.2.3.123124345235235`.
     - NOTE: A person may have multiple applications with different names so there may exist for example.
     - IN ADDITION: Multiple applications with attachments may get merged to the same folder

### TODO / issues / Help wanted

 - No GUI
 - no easy way to use/configure 
 - Does not use official APIs.
 - not configurable output target format (for example per-program folder for attachments)


## Misc
Likely the correct documentation path for a PROPER API: https://wiki.eduuni.fi/display/ophpolku/Hakeneet+ja+paikan+vastaanottaneet+%28kk%29+v4

Also check (api complains if you don't give caller-id):
https://github.com/Opetushallitus/dokumentaatio/blob/master/http.md

Misc links:

https://wiki.eduuni.fi/display/ophoppija/Hakemuspalvelun+REST+API

https://virkailija.opintopolku.fi/suoritusrekisteri/swagger/index.html#/kkhakijat/haeKkHakijat

https://koski.opintopolku.fi/koski/dokumentaatio/koodisto/oppiainematematiikka/latest

https://koski.opintopolku.fi/koski/dokumentaatio
