from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any
import aiohttp
import phonenumbers
from phonenumbers import carrier,geocoder,timezone

@dataclass
class ProviderResult:
    name:str|None=None
    carrier:str|None=None
    timezone:str|None=None
    location:str|None=None
    source:str="unknown"

class DirectoryProvider:
    """Optional provider adapter. It never fabricates caller identity."""
    def __init__(self):
        self.url=os.getenv("DIRECTORY_API_URL","").strip()
        self.key=os.getenv("DIRECTORY_API_KEY","").strip()
        self.header=os.getenv("DIRECTORY_API_AUTH_HEADER","Authorization").strip()
        self.bearer=os.getenv("DIRECTORY_API_BEARER","true").lower()=="true"
        self.timeout=float(os.getenv("DIRECTORY_API_TIMEOUT_SECONDS","8"))
    async def lookup(self,e164:str)->ProviderResult:
        if not self.url:return ProviderResult(source="not-configured")
        headers={}
        if self.key: headers[self.header]=f"Bearer {self.key}" if self.bearer else self.key
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as s:
                async with s.get(self.url,params={"phone":e164},headers=headers) as r:
                    if r.status!=200:return ProviderResult(source=f"http-{r.status}")
                    data=await r.json(content_type=None)
            return ProviderResult(name=data.get("name") or data.get("caller_name"),
                                  carrier=data.get("carrier"),timezone=data.get("timezone"),
                                  location=data.get("location") or data.get("region") or data.get("city"),
                                  source="directory")
        except (aiohttp.ClientError,TimeoutError,ValueError):
            return ProviderResult(source="provider-error")

def flag_for_region(region:str|None)->str:
    if not region or len(region)!=2:return ""
    return "".join(chr(127397+ord(c)) for c in region.upper())

def parse_number(raw:str,default_region:str="IN")->phonenumbers.PhoneNumber:
    cleaned=raw.strip().replace(" ","").replace("-","").replace("(","").replace(")","")
    if cleaned.isdigit() and len(cleaned)==10 and default_region=="IN": cleaned="+91"+cleaned
    elif cleaned.isdigit(): cleaned="+"+cleaned
    parsed=phonenumbers.parse(cleaned,default_region)
    if not phonenumbers.is_possible_number(parsed): raise ValueError("The number length/prefix is not possible.")
    if not phonenumbers.is_valid_number(parsed): raise ValueError("Invalid phone number.")
    return parsed

async def lookup_phone_number(raw_input:str,default_region:str="IN",directory:DirectoryProvider|None=None)->dict[str,Any]:
    try: parsed=parse_number(raw_input,default_region)
    except (phonenumbers.NumberParseException,ValueError) as exc:return {"valid":False,"error":str(exc)}
    e164=phonenumbers.format_number(parsed,phonenumbers.PhoneNumberFormat.E164)
    region=phonenumbers.region_code_for_number(parsed)
    country=geocoder.country_name_for_number(parsed,"en") or "Unknown"
    location=geocoder.description_for_number(parsed,"en") or country
    carrier_name=carrier.name_for_number(parsed,"en") or "Not found"
    zones=timezone.time_zones_for_number(parsed); tz=zones[0] if zones else "Not found"
    type_name={phonenumbers.PhoneNumberType.MOBILE:"Mobile",
               phonenumbers.PhoneNumberType.FIXED_LINE:"Fixed line",
               phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE:"Fixed line / mobile",
               phonenumbers.PhoneNumberType.VOIP:"VoIP",
               phonenumbers.PhoneNumberType.TOLL_FREE:"Toll free",
               phonenumbers.PhoneNumberType.PREMIUM_RATE:"Premium rate"}.get(phonenumbers.number_type(parsed),"Other")
    s1=await (directory or DirectoryProvider()).lookup(e164)
    s2=ProviderResult(carrier=carrier_name,timezone=tz,location=location,source="libphonenumber")
    return {"valid":True,"e164":e164,"digits_only":e164[1:],"country":country,"flag":flag_for_region(region),
            "number_type":type_name,"server_1":s1.__dict__,"server_2":s2.__dict__}
