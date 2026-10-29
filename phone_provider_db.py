"""Conservative carrier-prefix fallback data.

This is a fallback only. Mobile number portability means a prefix does not
prove the subscriber's current carrier, so callers must label it accordingly.
"""

INDIA_PREFIXES = {
    "810": "Airtel", "811": "Airtel", "812": "Airtel", "813": "Airtel",
    "814": "Airtel", "815": "Airtel", "816": "Airtel", "817": "Airtel",
    "818": "Airtel", "819": "Airtel",
    "820": "Airtel", "821": "Airtel", "822": "Airtel", "823": "Airtel",
    "824": "Airtel", "825": "Airtel", "826": "Airtel", "827": "Airtel",
    "828": "Airtel", "829": "Airtel",
    "830": "Jio", "831": "Jio", "832": "Jio", "833": "Jio", "834": "Jio",
    "835": "Jio", "836": "Jio", "837": "Jio", "838": "Jio", "839": "Jio",
    "840": "Jio", "841": "Jio", "842": "Jio", "843": "Jio", "844": "Jio",
    "845": "Jio", "846": "Jio", "847": "Jio", "848": "Jio", "849": "Jio",
    "850": "Jio", "851": "Jio", "852": "Jio", "853": "Jio", "854": "Jio",
    "855": "Jio", "856": "Jio", "857": "Jio", "858": "Jio", "859": "Jio",
    "860": "Jio", "861": "Jio", "862": "Jio", "863": "Jio", "864": "Jio",
    "865": "Jio", "866": "Jio", "867": "Jio", "868": "Jio", "869": "Jio",
    "870": "Jio", "871": "Jio", "872": "Jio", "873": "Jio", "874": "Jio",
    "875": "Jio", "876": "Jio", "877": "Jio", "878": "Jio", "879": "Jio",
    "880": "Jio", "881": "Jio", "882": "Jio", "883": "Jio", "884": "Jio",
    "885": "Jio", "886": "Jio", "887": "Jio", "888": "Jio", "889": "Jio",
    "890": "Jio", "891": "Jio", "892": "Jio", "893": "Jio", "894": "Jio",
    "895": "Jio", "896": "Jio", "897": "Jio", "898": "Jio", "899": "Jio",
}
# Deliberately conservative: libphonenumber remains the preferred source.

def get_prefix_carrier(e164: str, country_iso: str | None) -> str | None:
    if country_iso != "IN" or not e164.startswith("+91"):
        return None
    local = e164[3:]
    return INDIA_PREFIXES.get(local[:3])
