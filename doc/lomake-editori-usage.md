# Opintopolun hakemusten haku

## Virkailijoiden työskentely

- Esikäsittely: Ladataan/avataan hakemus, tulostetaan PDF, ladataan ja käydään läpi liitteet, oleelliset mergetään tulostettuun hakemus-PDF:ään -> tuloksena hakemus oleellisine liitteineen yhdessä pdf:ssä, joka on "helppo" käydä läpi
- Excelissä pidetään tilatietoja hakemuksen tarkastelun edistymisestä (opintopolku ilmeisesti tähän liian kömpelö/hidas?)
	- Työmäärä hajautetaan perustuen joihinkin hakijan attribuutteihin
- Meidän homma alun perin: ladata hakemusten liitteet ja asettaa ne hakijakohtaisiin kansioihin, koska opintopolun hitauden ja käyttöliittymän vuoksi homma oli todella hidasta
	- Liitteitä saa myös täydentää hakemuksen jätön jälkeen joko vapaaehtoisesti tai pyynnöstä -> tarve indikoida ja ladata uudet liitteet


## Järjestelmän datamalli

- Hakuja on useita
- Yhdessä haussa on useita hakukohteita
- Hakija tekee hakemuksen hakuun
	- Hakemus kohdistetaan tiettyihin hakukohteisiin
	- Yksi hakemus voi sisältää useita hakukohteita (Min. 1, max. kaikki hakukohteet haussa)
- Hakemuksessa on lomake (aka kysymykset)
	- Lomakkeen kentät ovat joko hakukohtaisia tai hakukohdekohtaisia
	- Hakemuksessa on myös vastaukset lomakkeen kenttiin
- Hakemuksessa on liitteitä, joilla on tila (tarkistettu jne)
	- Liitteet ovat hakukohdekohtaisia (eri hakukohteet haluavat eri liitteitä, osa samoja keskenään)

## Tunnisteet

- haku-oid (haun id)
- hakukohde-oid (hakukohteen id)
- person_oid=application["person"]["oid"] (henkilön id, joskus sama kuin oppijanumero, mutta ei välttämättä?)
- application_oid = application["key"] (
- file_guid = liitetiedoston yksilöivä tunniste

## Lomake-editori API

### Lista haun/hakukohteen hakemuksista
Req: POST "/lomake-editori/api/applications/list"
Parametrit: hakukohde-oid (tai haku-oid, jos kaikki haun hakukohteet) + offset + muita filttereitä json-muodossa (ks. constans.py)
Res: Lista hakemuksista perustiedoilla, palasissa, täytyy käyttää offsetteja, jos hakemuksia suuri määrä

### Hakemuksen yksityiskohdat
Req: GET https://virkailija.opintopolku.fi/lomake-editori/api/applications/{application_oid}"
Res: JSON-muodossa hakemuksen yksityiskohdat, sis. **kaikki** hakijan hakukohteet kys. haussa

- Hakemuksessa lomaketiedot (form), jossa kuvattu lomakkeen elementit sekä se, mihin hakukohteisiin lomakkeen kentät ovat relevantteja (form>content[]>children*[]>belongs-to-hakukohteet)
- Vastaukset erikseen (answers-taulukko). key-attribuutti viittaa formin id:hen
- attachment-reviews: Liitteiden tilatiedot hakukohdekohtaisesti (eri hakukohteet haluavat eri liitteitä) -> avaimena liitteiden GUID

### Liitteet

- Hakemuksen yksityiskohdat -> attachment-reviews -> saa hakukohteen liitteiden GUID
- Req: GET https://virkailija.opintopolku.fi/lomake-editori/api/files/content/{file_guid} -- lataa liite
- Req: https://virkailija.opintopolku.fi/lomake-editori/api/files/metadata -- liitteen metadata (kuvaus) -- ei muistikuvaa käyttötavasta


### Summa summarum

Hakija täyttää hakemuksen avoimeen hakuun. Haussa on useita hakukohteita, jotka hakija valitsee. Lomakkeen täytettävät elementit ja liitteet ovat paikoitellen riippuvaisia hakukohteista.

Yhdellä hakijalla on yksi hakemus yhteen hakuun. Yhdessä haussa on useita hakukohteita. Yksi hakemus voi sisältää useita hakukohteita (Min. 1, max. kaikki hakukohteet haussa)
