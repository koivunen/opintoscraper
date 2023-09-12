LIST_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/applications/list"
APPLICATION_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/applications/{oid}"
ME_INFO_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/user-info"
METADATA_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/files/metadata"
FILE_DOWNLOAD_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/files/content/{file_guid}"
ME2_INFO_URL="https://virkailija.opintopolku.fi/kayttooikeus-service/cas/me"
OUTPUT_PATH="/kvhaku/tmp/output_test/"
OUTPUT_PATH="/kvhaku/production_samba/kv_23/"
DATABASE_PATH="/kvhaku/tmp/kv_23_database.cache"

EXCEL_ONLY=False # skip attachment downloading to refresh excel
DB_ONLY=True

DISABLE_EXCEL=True

#Testing
#OUTPUT_PATH="output_delme"
#DATABASE_PATH="database_delme"

# Korkeakoulujen kevään 2023 ensimmäinen yhteishaku
TARGET_OIDS = {
    "1.2.246.562.20.00000000000000019775": "suscity",

    "1.2.246.562.20.00000000000000019471": "biomed",
    "1.2.246.562.20.00000000000000019472": "physchem",
    "1.2.246.562.20.00000000000000019473": "food",
    "1.2.246.562.20.00000000000000019474": "health",
    "1.2.246.562.20.00000000000000019475": "materials",
    "1.2.246.562.20.00000000000000019476": "mecheng",
    "1.2.246.562.20.00000000000000019477": "biosci",
    "1.2.246.562.20.00000000000000019478": "ict",
}

#TODO: excel autogen
#print("\t".join(TARGET_OIDS.values()))

true=True
false=False
null=None
LIST_URL_QUERY={
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
    "hakukohde-oid": "FILL_ME"
}

#TODO: hakukohderyhma-oid: "1.2.246.562.28.65534771657"  yliopisto, 1. yhteishaun matlu + tek + biomedical 2022?
#      haku-oid: "1.2.246.562.29.00000000000000002175"     ?????????????
