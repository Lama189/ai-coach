import re


def normalize_phone(phone_number: str) -> str | None:
    if phone_number.startswith("998"):
        phone_number = "+" + phone_number
    elif phone_number.startswith("0"):
        phone_number = "+998" + phone_number[1:]
    elif not phone_number.startswith("+"):
        phone_number = "+" + phone_number

    if not re.fullmatch(r"\+998\d{9}", phone_number):
        return None

    return phone_number