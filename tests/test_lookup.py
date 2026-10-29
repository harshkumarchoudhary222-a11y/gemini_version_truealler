import asyncio
from lookup_service import lookup_phone_number,parse_number

def test_indian_number_normalization():
    n=parse_number("8101115026")
    assert n.country_code==91
    assert n.national_number==8101115026

def test_international_number():
    assert parse_number("+919876543210").country_code==91

def test_invalid_number():
    result=asyncio.run(lookup_phone_number("123"))
    assert result["valid"] is False
