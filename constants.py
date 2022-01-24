LIST_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/applications/list"
APPLICATION_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/applications/{oid}"
ME_INFO_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/user-info"
METADATA_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/files/metadata"
FILE_DOWNLOAD_URL = "https://virkailija.opintopolku.fi/lomake-editori/api/files/content/{0}"
ME2_INFO_URL="https://virkailija.opintopolku.fi/kayttooikeus-service/cas/me"

TARGET_OIDS = {
    "1.2.246.562.20.00000000000000002202": "biomed",
    "1.2.246.562.20.00000000000000002276": "biosci",
    "1.2.246.562.20.00000000000000002301": "food",
    "1.2.246.562.20.00000000000000002316": "physchem",
    "1.2.246.562.20.00000000000000002378": "ict",
    "1.2.246.562.20.00000000000000002599": "health",
    "1.2.246.562.20.00000000000000002600": "materials",
    "1.2.246.562.20.00000000000000002601": "mecheng"
}

LIST_URL_QUERY={
    "sort": {
        "order-by": "applicant-name",
        "order": "asc"
    },
    "attachment-review-states": {},
    "option-answers": {},
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
                "unreviewed": True,
                "fulfilled": True,
                "unfulfilled": True
            },
            "degree-requirement": {
                "unreviewed": True,
                "fulfilled": True,
                "unfulfilled": True
            },
            "eligibility-set-automatically": {
                "yes": True,
                "no": True
            },
            "only-identified": {
                "identified": True,
                "unidentified": True
            },
            "only-ssn": {
                "with-ssn": True,
                "without-ssn": True
            },
            "active-status": {
                "active": True,
                "passive": False
            },
            "question-answer-filtering-options": {},
            "eligibility-state": {
                "unreviewed": True,
                "eligible": True,
                "uneligible": True,
                "conditionally-eligible": True
            },
            "attachment-review-states": {},
            "base-education": {
                "pohjakoulutus_kk_ulk": True,
                "pohjakoulutus_lk": True,
                "pohjakoulutus_amp": True,
                "pohjakoulutus_kk": True,
                "pohjakoulutus_amt": True,
                "pohjakoulutus_ulk": True,
                "pohjakoulutus_muu": True,
                "pohjakoulutus_avoin": True,
                "pohjakoulutus_yo_ammatillinen": True,
                "pohjakoulutus_am": True,
                "pohjakoulutus_yo_ulkomainen": True,
                "pohjakoulutus_yo": True,
                "pohjakoulutus_yo_kansainvalinen_suomessa": True,
                "pohjakoulutus_amv": True
            },
            "payment-obligation": {
                "unreviewed": True,
                "obligated": True,
                "not-obligated": True
            }
        }
    },
    "hakukohde-oid": "1.2.246.562.20.00000000000000002301"
}