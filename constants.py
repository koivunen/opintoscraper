import os 

TARGETNAME=os.getenv("TARGETORG")
TARGET=["test","east","invest","edlearn","tse","med","scitech"].index(TARGETNAME)


# Mode matrix
EXCEL_ONLY=		[False,False,False,False,True,False,False][TARGET] # skip attachment downloading to refresh excel
DISABLE_EXCEL=	[False,False,False,False,False,False,False][TARGET]
DB_ONLY=		[False,False,False,False,False,False,False][TARGET]


TARGET_OIDS = [{
 '1.2.246.562.20.00000000000000036553': 'EAST', #test
 '1.2.246.562.20.00000000000000039962': 'Biomed' #test
},{
 '1.2.246.562.20.00000000000000036553': 'EAST'
},{
 '1.2.246.562.20.00000000000000036552': 'IINWS'
},{
'1.2.246.562.20.00000000000000036551': 'Edu'
},{
 '1.2.246.562.20.00000000000000036548': 'Futu',
 '1.2.246.562.20.00000000000000036549': 'GIM',
},{
 '1.2.246.562.20.00000000000000036555': 'Neuro',
 '1.2.246.562.20.00000000000000038065': 'Mental',
 '1.2.246.562.20.00000000000000039962': 'Biomed'
},{
}][TARGET]

DATABASE_PATH=f"/kvhaku/tmp/{TARGETNAME}_kv_database.cache"

#TODO: depreciate
DATABASE_PATH=[
"/kvhaku/tmp/test_kv_database.cache",
"/kvhaku/tmp/east_kv_24_database.cache",
"/kvhaku/tmp/invest_kv_24_database.cache",
"/kvhaku/tmp/edlearn_kv_24_database.cache",
"/kvhaku/tmp/tse_kv_24_database.cache",
"/kvhaku/tmp/med_kv_24_database.cache",
"/kvhaku/tmp/sci_kv_24_database.cache"
][TARGET]


OUTPUT_PATH=f"/kvhaku/production_samba_{TARGETNAME}/kv24"

#TODO: depreciate
OUTPUT_PATH=[
	"/kvhaku/tmp/test",
	"/kvhaku/production_samba_east/kv24/",
	"/kvhaku/production_samba_invest/kv24/",
	"/kvhaku/production_samba_edlearn/kv24/",
	"/kvhaku/production_samba_tse/kv24/",
	"/kvhaku/production_samba_med/kv24/", # actually mounted from [...]/att/
	"/kvhaku/production_samba/kv24/"
][TARGET]

EXCEL_BASEPATH=[
	r'\\utu.fi\taltio\EAST\test_delme',
	r'\\utu.fi\taltio\EAST\kv24',
	r'\\utu.fi\taltio\INVEST MDP SELECTION\kv24',
	r'\\utu.fi\taltio\EDLEARN\kv24',
	r"\\utu.fi\taltio\TSE master's applications 2024\kv24",
	r'\\utu.fi\taltio\MED Masters admissions\att\kv24',
	r'\\utu.fi\taltio\SCITECH Masters admissions\att\kv24',
][TARGET] + "\\"


#Testing
#OUTPUT_PATH="output_delme"
#DATABASE_PATH="database_delme"



#TODO: excel autogen
#print("\t".join(TARGET_OIDS.values()))
def gen_LIST_URL_QUERY(OID):
	true=True
	false=False
	null=None
	return {
		"sort": {
			"order-by": "applicant-name",
			"order": "asc"
		},
		"attachment-review-states": {},
		"option-answers": [],
		"states-and-filters": {
			"attachment-states-to-include": [
				"not-checked",
				"checked",
				"incomplete-attachment",
				"attachment-missing",
				"overdue",
				"no-requirements"
			],
			"processing-states-to-include": [
				"unprocessed",
				"processing",
				"invited-to-interview",
				"invited-to-exam",
				"evaluating",
				"valintaesitys",
				"processed",
				"information-request"
			],
			"filters": {
				"language-requirement": {
					"unreviewed": true,
					"fulfilled": true,
					"unfulfilled": true
				},
				"degree-requirement": {
					"unreviewed": true,
					"fulfilled": true,
					"unfulfilled": true
				},
				"eligibility-set-automatically": {
					"yes": true,
					"no": true
				},
				"only-identified": {
					"identified": true,
					"unidentified": true
				},
				"only-ssn": {
					"with-ssn": true,
					"without-ssn": true
				},
				"active-status": {
					"active": true,
					"passive": false
				},
				"question-answer-filtering-options": {},
				"eligibility-state": {
					"unreviewed": true,
					"eligible": true,
					"uneligible": true,
					"conditionally-eligible": true
				},
				"attachment-review-states": {},
				"only-edited-hakutoiveet": {
					"edited": true,
					"unedited": true
				},
				"base-education": {
					"pohjakoulutus_kk_ulk": true,
					"pohjakoulutus_lk": true,
					"pohjakoulutus_amp": true,
					"pohjakoulutus_kk": true,
					"pohjakoulutus_amt": true,
					"pohjakoulutus_ulk": true,
					"pohjakoulutus_muu": true,
					"pohjakoulutus_avoin": true,
					"pohjakoulutus_yo_ammatillinen": true,
					"pohjakoulutus_am": true,
					"pohjakoulutus_yo_ulkomainen": true,
					"pohjakoulutus_yo": true,
					"pohjakoulutus_yo_kansainvalinen_suomessa": true,
					"pohjakoulutus_amv": true
				},
				"payment-obligation": {
					"unreviewed": true,
					"obligated": true,
					"not-obligated": true
				}
			},
			"school-filter": null,
			"classes-of-school": null
		},
		"hakukohde-oid": OID
	}
LIST_URL_QUERY=gen_LIST_URL_QUERY("FILL_ME")



LIST_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/applications/list"
APPLICATION_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/applications/{oid}"
ME_INFO_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/user-info"
METADATA_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/files/metadata"
FILE_DOWNLOAD_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/files/content/{file_guid}"
ME2_INFO_URL="https://virkailija.opintopolku.fi/kayttooikeus-service/cas/me"

#TODO: hakukohderyhma-oid: "1.2.246.562.28.65534771657"  yliopisto, 1. yhteishaun matlu + tek + biomedical 2022?
#      haku-oid: "1.2.246.562.29.00000000000000002175"     ?????????????
