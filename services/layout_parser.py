import re
import math

from rapidfuzz import fuzz

# Parser posisi kata: terima ocr_result["words"] (list dict
# text/left/top/width/height/conf), kembalikan dict per field
# {value, unit, unit_valid} - lihat parse_document() di akhir file.

ROW_THRESHOLD = 18

COLUMN_THRESHOLD = 120

RIGHT_LIMIT = 260

BOTTOM_LIMIT = 70

FUZZY_THRESHOLD = 75



# substitusi huruf->angka (o/l/i/s ke 0/1/1/5), tapi HANYA untuk
# token yang didominasi angka (mis. "l0"->"10") - jangan diterapkan
# ke kata label biasa ("Protein" dst), lihat clean_text() di bawah
OCR_FIX = {

    "O": "0",
    "o": "0",

    "I": "1",
    "l": "1",
    "|": "1",

    "S": "5",

}



# FIELD ALIAS

FIELDS = {

    "energi":[

        "energi",

        "energi total",

        "energy",

        "total energy",

        "total energi"

    ],

    "protein":[

        "protein"

    ],

    "lemak_total":[

        "lemak total",

        "total lemak",

        "total fat"

    ],

    "lemak_jenuh":[

        "lemak jenuh",

        "saturated fat"

    ],

    "lemak_trans":[

        "lemak trans",

        "trans fat"

    ],

    "kolesterol":[

        "kolesterol",

        "cholesterol"

    ],

    "karbohidrat_total":[

        "karbohidrat total",

        "karbohidrat",

        "total carbohydrate",

        "total karbohidrat"

    ],

    "serat":[

        "serat",

        "serat pangan",

        "dietary fiber",

        "fiber"

    ],

    "gula_total":[

        "gula",

        "gula total",

        "total sugars",

        "sugars"

    ],

    "sukrosa":[

        "sukrosa",

        "sucrose"

    ],

    "natrium":[

        "natrium",

        "sodium",

        "garam"

    ],

    "takaran_saji":[

        "takaran saji",

        "serving size"

    ],

    "sajian_per_kemasan":[

        "sajian per kemasan",

        "servings per container"

    ]

}



# VALID UNIT

VALID_UNITS = {

    "energi":[

        "kkal",

        "kcal",

        "kal"

    ],

    "protein":[

        "g"

    ],

    "lemak_total":[

        "g"

    ],

    "lemak_jenuh":[

        "g"

    ],

    "lemak_trans":[

        "g"

    ],

    "kolesterol":[

        "mg"

    ],

    "karbohidrat_total":[

        "g"

    ],

    "serat":[

        "g"

    ],

    "gula_total":[

        "g"

    ],

    "sukrosa":[

        "g"

    ],

    "natrium":[

        "mg"

    ],

    "takaran_saji":[

        "g",

        "ml"

    ],

    "sajian_per_kemasan":[

        "porsi",

        "serving"

    ]

}



# CLEAN OCR

def clean_text(text):

    lowered = text.strip().lower()

    # koma desimal aman diterapkan ke teks apapun ("10,85" -> "10.85")
    lowered = lowered.replace(",", ".")

    substituted = lowered

    for old, new in OCR_FIX.items():

        substituted = substituted.replace(old.lower(), new)

    digit_count = sum(ch.isdigit() for ch in substituted)

    # pakai versi substitusi cuma kalau token didominasi angka,
    # supaya kata label ("protein", "sodium") tidak ikut rusak
    if digit_count > 0 and digit_count >= len(substituted) - 1:

        return substituted

    return lowered



# NORMALIZE WORD

def normalize_word(word):

    word["text"] = clean_text(

        word["text"]

    )

    return word



# NORMALIZE OCR

def normalize_words(words):

    result = []

    for word in words:

        if word["text"].strip() == "":
            continue

        result.append(

            normalize_word(word)

        )

    return result



# BUILD ROWS

def build_rows(words):

    rows = []

    words = sorted(

        words,

        key=lambda x: (

            x["top"],

            x["left"]

        )

    )

    for word in words:

        found = False

        for row in rows:

            if abs(

                row["top"] -

                word["top"]

            ) < ROW_THRESHOLD:

                row["words"].append(word)

                row["top"] = int(

                    sum(

                        w["top"]

                        for w in row["words"]

                    )

                    /

                    len(

                        row["words"]

                    )

                )

                found = True

                break

        if not found:

            rows.append({

                "top": word["top"],

                "words": [

                    word

                ]

            })

    return rows



# SORT ROWS

def sort_rows(rows):

    for row in rows:

        row["words"] = sorted(

            row["words"],

            key=lambda x: x["left"]

        )

    return rows



# ROW TO TEXT

def row_to_text(row):

    return " ".join(

        w["text"]

        for w in row["words"]

    )



# MERGE ROW

def merge_rows(rows):

    merged = []

    for row in rows:

        merged.append({

            "top": row["top"],

            "text": row_to_text(row),

            "words": row["words"]

        })

    return merged

# FIND BEST KEYWORD IN ROW

def find_row_keyword(row_text, aliases):

    best_score = 0
    best_alias = None

    text = clean_text(row_text)

    for alias in aliases:

        score = fuzz.partial_ratio(

            text,

            alias

        )

        if score > best_score:

            best_score = score
            best_alias = alias

    return best_alias, best_score


# FIND ROW BY FIELD

def find_field_row(rows, aliases):

    best = None
    best_score = 0

    for row in rows:

        alias, score = find_row_keyword(

            row["text"],

            aliases

        )

        if score > best_score:

            best_score = score
            best = row

    if best_score < FUZZY_THRESHOLD:

        return None

    return best


# SEARCH WORDS RIGHT

def search_right(row, keyword_left=0):

    result = []

    for word in row["words"]:

        if word["left"] <= keyword_left:

            continue

        result.append(word)

    return sorted(

        result,

        key=lambda x: x["left"]

    )


# SEARCH NEXT ROW

def search_next_rows(rows, current_top):

    result = []

    for row in rows:

        if row["top"] <= current_top:

            continue

        distance = row["top"] - current_top

        if distance > BOTTOM_LIMIT:

            continue

        result.append(row)

    return sorted(

        result,

        key=lambda x: x["top"]

    )


# FIND KEYWORD POSITION

def keyword_position(row, aliases):

    best = None
    best_score = 0

    for word in row["words"]:

        txt = clean_text(

            word["text"]

        )

        for alias in aliases:

            score = fuzz.partial_ratio(

                txt,

                alias

            )

            if score > best_score:

                best_score = score
                best = word

    return best


# OCR NUMBER FIX

def normalize_number(text):

    # pakai clean_text() yang sudah aman, jangan substitusi ulang di sini
    return clean_text(text)


# EXTRACT NUMBER

NUMBER_PATTERN = re.compile(

    r"\d+(?:\.\d+)?"

)


def extract_number(words):

    for word in words:

        txt = normalize_number(

            word["text"]

        )

        m = NUMBER_PATTERN.search(txt)

        if m:

            value = m.group()

            try:

                value = float(value)

                if value.is_integer():

                    value = int(value)

                return value

            except:

                pass

    return None


# UNIT PATTERN

UNIT_PATTERN = re.compile(

    r"(kkal|kcal|kal|mg|mcg|µg|ug|g|gram|ml|%)",

    re.IGNORECASE

)


# EXTRACT UNIT

def extract_unit(words):

    for word in words:

        txt = clean_text(

            word["text"]

        )

        m = UNIT_PATTERN.search(txt)

        if m:

            return m.group().lower()

    return ""


# AUTO UNIT

def infer_unit(field):

    if field == "energi":

        return "kkal"

    if field == "natrium":

        return "mg"

    if field == "kolesterol":

        return "mg"

    if field == "takaran_saji":

        return "g"

    if field == "sajian_per_kemasan":

        return "porsi"

    return "g"


# UNIT VALIDATION

def validate_unit(field, unit):

    valid = VALID_UNITS.get(

        field,

        []

    )

    return unit in valid


# CONFIDENCE

def candidate_confidence(

    keyword_score,

    value,

    unit_valid

):

    score = 0

    score += keyword_score * 0.6

    if value is not None:

        score += 25

    if unit_valid:

        score += 15

    return round(

        min(score, 100),

        2

    )


# BUILD CANDIDATE

def build_candidate(

    field,

    value,

    unit,

    keyword_score

):

    if unit == "":

        unit = infer_unit(

            field

        )

    unit_valid = validate_unit(

        field,

        unit

    )

    confidence = candidate_confidence(

        keyword_score,

        value,

        unit_valid

    )

    return {

        "value": value,

        "unit": unit,

        "unit_valid": unit_valid,

        "confidence": confidence

    }
    
def parse_field(field_name, rows, aliases):
    """Cari nilai & satuan suatu field dari baris OCR (cari ke kanan lalu ke bawah)."""

    row = find_field_row(rows, aliases)

    if not row:
        return build_candidate(field_name, None, "", 0)

    _, keyword_score = find_row_keyword(row["text"], aliases)
    kw_node = keyword_position(row, aliases)
    kw_left = kw_node["left"] if kw_node else 0

    candidates = []

    # strategi 1: cari di sebelah kanan keyword (layout linear)
    right_words = search_right(row, kw_left)
    if right_words:
        val = extract_number(right_words)
        unit = extract_unit(right_words)

        if val is not None:
            c_right = build_candidate(field_name, val, unit, keyword_score)
            candidates.append(c_right)

        # token gabungan angka+satuan menyatu, mis. "67g"
        for w in right_words:
            w_text = clean_text(w["text"])
            num_match = NUMBER_PATTERN.search(normalize_number(w["text"]))
            unit_match = UNIT_PATTERN.search(w_text)
            
            if num_match and unit_match:
                try:
                    c_val = float(num_match.group())
                    if c_val.is_integer():
                        c_val = int(c_val)
                    c_combined = build_candidate(field_name, c_val, unit_match.group().lower(), keyword_score)
                    candidates.append(c_combined)
                except ValueError:
                    pass

    # strategi 2: cari di baris bawahnya (layout tabel), maks 3 baris terdekat
    next_rows = search_next_rows(rows, row["top"])

    for next_r in next_rows[:3]:
        val = extract_number(next_r["words"])
        unit = extract_unit(next_r["words"])

        if val is not None:
            c_bottom = build_candidate(field_name, val, unit, keyword_score)
            candidates.append(c_bottom)
            break  # berhenti di baris pertama yang mengandung angka

    if not candidates:
        # nama field ketemu, tapi tidak ada angka/satuan di sekitarnya
        return build_candidate(field_name, None, "", keyword_score)

    return max(candidates, key=lambda x: x["confidence"])


def parse_document(ocr_words, field_config=FIELDS, debug=False):
    """Proses seluruh token OCR jadi dict nutrisi terstruktur per field."""

    words = normalize_words(ocr_words)
    rows = build_rows(words)
    rows = sort_rows(rows)
    rows = merge_rows(rows)  # menambahkan key "text" ke tiap row

    if debug:
        print(f"[DEBUG] Berhasil membangun {len(rows)} baris dari {len(ocr_words)} token OCR.")

    result = {}

    for field_name, aliases in field_config.items():
        parsed = parse_field(field_name, rows, aliases)
        result[field_name] = parsed

        if debug:
            status = "SUKSES" if parsed["value"] is not None else "GAGAL"
            print(f"[DEBUG] {field_name.upper():<20} | Status: {status:<6} | Value: {str(parsed['value']):<6} | Unit: {parsed['unit']:<4} | Conf: {parsed['confidence']}%")

    return result

