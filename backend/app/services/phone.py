"""Phone number normalisation."""

import phonenumbers


def normalise_phone(raw: str | None, region: str = "IE") -> str | None:
    """Return E.164 form or None when unparseable."""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        parsed = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException:
        return raw
    if not phonenumbers.is_valid_number(parsed):
        return raw
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
