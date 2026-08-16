import math

# BATAS WAJAR PER FIELD
LIMITS = {
    "energi": (0, 5000),
    "protein": (0, 500),
    "lemak_total": (0, 500),
    "lemak_jenuh": (0, 500),
    "lemak_trans": (0, 500),
    "kolesterol": (0, 5000),
    "karbohidrat_total": (0, 1000),
    "serat": (0, 200),
    "gula_total": (0, 500),
    "sukrosa": (0, 500),
    "natrium": (0, 10000),
    "takaran_saji": (0, 5000),
    "sajian_per_kemasan": (0, 500)
}

# field dengan satuan gram di mana pola "g" (satuan) terbaca jadi digit "9" 
GRAM_FIELDS_G9 = [
    "protein",
    "lemak_total",
    "lemak_jenuh",
    "lemak_trans",
    "karbohidrat_total",
    "serat",
    "gula_total",
    "sukrosa",
]

# STATUS
STATUS_VALID = "Valid"
STATUS_EMPTY = "Kosong"
STATUS_UNIT = "Unit Salah"
STATUS_RANGE = "Di Luar Batas"
STATUS_LOGIC = "Tidak Logis"
STATUS_WARNING = "Perlu Dicek"
STATUS_CORRECTED = "Dikoreksi Otomatis"
STATUS_REJECTED = "Ditolak (Di Luar Nalar)"

# COBA PERBAIKI POLA "g" TERBACA JADI "9"
def try_fix_g9_misread(field, value):

    if field not in GRAM_FIELDS_G9:
        return None

    if value is None:
        return None

    try:
        text = str(int(value)) if float(value).is_integer() else str(value)
    except (TypeError, ValueError):
        return None

    if len(text) < 2 or not text.endswith("9"):
        return None

    corrected_text = text[:-1]

    try:
        corrected = float(corrected_text)
    except ValueError:
        return None

    minimum, maximum = LIMITS[field]

    if minimum <= corrected <= maximum:
        return corrected

    return None

# RANGE CHECK
def check_range(field, value):

    if value is None:
        return STATUS_EMPTY

    minimum, maximum = LIMITS[field]

    if value < minimum:
        return STATUS_RANGE

    if value > maximum:
        return STATUS_RANGE

    return STATUS_VALID

# UNIT CHECK
def check_unit(item):

    if not item["unit_valid"]:

        return STATUS_UNIT

    return STATUS_VALID

# Energi harus mendekati (4*protein + 4*karbo + 9*lemak), toleransi 25%
def check_energy_formula(data):

    protein = data["protein"]["value"] or 0

    carb = data["karbohidrat_total"]["value"] or 0

    fat = data["lemak_total"]["value"] or 0

    energy = data["energi"]["value"]

    if energy is None:
        return STATUS_EMPTY

    estimate = (

        protein * 4 +

        carb * 4 +

        fat * 9

    )

    if estimate == 0:

        return STATUS_WARNING

    error = abs(

        estimate -

        energy

    ) / estimate

    if error > 0.25:

        return STATUS_WARNING

    return STATUS_VALID

# RELATIONSHIP CHECK
def relationship_check(data):

    issues = []

    carb = data["karbohidrat_total"]["value"]

    fiber = data["serat"]["value"]

    sugar = data["gula_total"]["value"]

    sucrose = data["sukrosa"]["value"]

    fat = data["lemak_total"]["value"]

    saturated = data["lemak_jenuh"]["value"]

    if carb is not None:

        if fiber is not None:

            if fiber > carb:

                issues.append(

                    "Serat > Karbohidrat"

                )

        if sugar is not None:

            if sugar > carb:

                issues.append(

                    "Gula > Karbohidrat"

                )

        if sucrose is not None:

            if sucrose > carb:

                issues.append(

                    "Sukrosa > Karbohidrat"

                )

    if fat is not None:

        if saturated is not None:

            if saturated > fat:

                issues.append(

                    "Lemak Jenuh > Lemak Total"

                )

    return issues

# SERVING CHECK
def serving_check(data):

    serving = data["takaran_saji"]["value"]

    protein = data["protein"]["value"]

    carb = data["karbohidrat_total"]["value"]

    fat = data["lemak_total"]["value"]

    if serving is None:

        return []

    issues = []

    total = 0

    for x in [

        protein,

        carb,

        fat

    ]:

        if x is not None:

            total += x

    if total > serving:

        issues.append(

            "Protein + Karbohidrat + Lemak > Takaran Saji"

        )

    return issues

# MAIN VALIDATION
def validate(data):

    result = {}

    for field, item in data.items():

        value = item["value"]

        status = check_range(
            field,
            value
        )

        if status == STATUS_RANGE:

            # coba koreksi pola "g" terbaca "9"
            corrected = try_fix_g9_misread(field, value)

            if corrected is not None:
                value = corrected
                status = STATUS_CORRECTED
            else:
                value = None
                status = STATUS_REJECTED

        elif status == STATUS_VALID:

            status = check_unit(item)

        result[field] = {
            **item,
            "value": value,
            "status": status
        }

    result["energi"]["energy_check"] = check_energy_formula(data)

    logic = []

    logic.extend(

        relationship_check(data)

    )

    logic.extend(

        serving_check(data)

    )

    result["validation"] = {
        "logic_issue": logic,
        "passed": len(logic) == 0
    }

    return result

# DEBUG
if __name__ == "__main__":

    sample = {
        "energi":{"value":622,"unit_valid":True},
        "protein":{"value":18,"unit_valid":True},
        "lemak_total":{"value":47,"unit_valid":True},
        "lemak_jenuh":{"value":20,"unit_valid":True},
        "lemak_trans":{"value":0,"unit_valid":True},
        "kolesterol":{"value":0,"unit_valid":True},
        "karbohidrat_total":{"value":33,"unit_valid":True},
        "serat":{"value":2,"unit_valid":True},
        "gula_total":{"value":5,"unit_valid":True},
        "sukrosa":{"value":3,"unit_valid":True},
        "natrium":{"value":944,"unit_valid":True},
        "takaran_saji":{"value":100,"unit_valid":True},
        "sajian_per_kemasan":{"value":1,"unit_valid":True}
    }

    from pprint import pprint

    pprint(validate(sample))