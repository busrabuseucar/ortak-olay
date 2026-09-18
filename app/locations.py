"""Conservative code conflict check, not geocoding or proof of place identity."""
import re
import unicodedata

# Only complete structured labels are parsed; no guesses from report prose.
KINDS = {
    'shelter': 'shelter', 'barınak': 'shelter', 'barinak': 'shelter', 'καταφυγιο': 'shelter',
    'school': 'school', 'okul': 'school', 'okulu': 'school', 'σχολειο': 'school',
    'camp': 'camp', 'kamp': 'camp', 'kampı': 'camp', 'καταυλισμος': 'camp',
}
# Visually corresponding single-letter labels only, not general transliteration.
GREEK_CODES = str.maketrans({'α': 'a', 'β': 'b', 'ε': 'e', 'ζ': 'z', 'η': 'h', 'ι': 'i', 'κ': 'k',
                              'μ': 'm', 'ν': 'n', 'ο': 'o', 'ρ': 'p', 'τ': 't', 'υ': 'y', 'χ': 'x'})


def site_code(label):
    label = ''.join(c for c in unicodedata.normalize('NFKD', label.casefold()) if not unicodedata.combining(c))
    parts = label.strip().split()
    kind = None
    if len(parts) == 1:
        code = parts[0]
    elif len(parts) == 2 and parts[0] in KINDS:
        kind, code = KINDS[parts[0]], parts[1]
    elif len(parts) == 2 and parts[1] in KINDS:
        kind, code = KINDS[parts[1]], parts[0]
    else:
        return None
    # Single Latin/Greek letter or ASCII integer; don't reinterpret place names.
    if not re.fullmatch(r'[a-zα-ω]|[0-9]{1,6}', code):
        return None
    return kind, code.translate(GREEK_CODES)


def code_conflict(left, right):
    a, b = site_code(left), site_code(right)
    if not a or not b:
        return False  # Unknown is not evidence of a conflict or a match.
    kind_a, code_a = a
    kind_b, code_b = b
    if kind_a and kind_b and kind_a != kind_b:
        return False  # Cross-type labels need human interpretation.
    return code_a != code_b
