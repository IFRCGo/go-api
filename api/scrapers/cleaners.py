import re
from datetime import datetime


def clean_number(num_in_str):
    if not num_in_str:
        return None

    regex = "\\d{1,3}(,\\d{3})*(\\.\\d+)?"  # ex.: 123,123.12
    match = re.search(regex, num_in_str)
    if match:
        try:
            num = int(re.sub(",", "", match.group()))
            return num
        except Exception:
            return None
    else:
        return None


def clean_appeal_code(appeal_code):
    if not appeal_code:
        return None

    regex = "MDR.{5}"
    match = re.search(regex, appeal_code.replace(" ", ""))  # elimate surplus spaces via this replace from the raw
    if match:
        return match.group()[:20]  # Substring at 20 because of max_length of appeal_code
    else:
        return None


def clean_date(date_in_str):
    if not date_in_str:
        return None

    # could use '\\d{1,2}(st|th)?...' if needed
    regex = "\\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) \\d{4}"
    match = re.search(regex, date_in_str)
    if match:
        try:
            date = datetime.strptime(match.group(), "%d %B %Y")
            return date
        except Exception:
            return None
    else:
        return None
