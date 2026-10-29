"""Conservative carrier-prefix fallback adapted from the public GhostIntel
phone provider table. This is only a fallback: mobile number portability
means a prefix does not prove the subscriber's current carrier.
"""

INDIA_PREFIXES = {
    "9810": "Airtel", "9811": "Airtel", "9812": "Airtel",
    "9818": "Airtel", "9819": "Airtel",
    "9820": "Vodafone Idea", "9821": "Vodafone Idea",
    "9822": "Vodafone Idea", "9824": "Vodafone Idea", "9825": "Vodafone Idea",
    "9830": "Vodafone Idea", "9831": "Vodafone Idea",
    "9832": "Vodafone Idea", "9833": "Vodafone Idea", "9834": "Vodafone Idea",
    "9870": "Jio", "9871": "Jio", "9872": "Jio",
    "9873": "Jio", "9874": "Jio",
    "8888": "BSNL", "8889": "BSNL", "8890": "BSNL",
}

def get_prefix_carrier(e164: str, country_iso: str | None) -> str | None:
    if country_iso != "IN" or not e164.startswith("+91"):
        return None
    return INDIA_PREFIXES.get(e164[3:7])
