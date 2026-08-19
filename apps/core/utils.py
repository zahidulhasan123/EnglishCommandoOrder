import re


def normalize_bd_phone(phone: str) -> str:
    cleaned = re.sub(r"\D", "", phone or "")
    if cleaned.startswith("880"):
        cleaned = "0" + cleaned[3:]
    if cleaned.startswith("+880"):
        cleaned = "0" + cleaned[4:]
    if cleaned.startswith("01") and len(cleaned) == 11:
        return cleaned
    return cleaned
