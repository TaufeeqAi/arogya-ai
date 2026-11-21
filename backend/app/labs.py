"""Lab test catalogue: canonical codes, body-system grouping, lab reference ranges and plain-language explanations.
Explanations describe what a test MEASURES (education), never what a result means for the patient (no diagnosis)."""
from __future__ import annotations

SYSTEMS = [
    ("sugar", "Sugar level", "🩸", "Blood sugar control"),
    ("heart", "Heart", "❤️", "Cholesterol & lipid profile"),
    ("liver", "Liver", "🫁", "Liver function"),
    ("kidney", "Kidney", "🫘", "Kidney function"),
    ("blood", "Hemogram", "🔬", "Complete blood count"),
    ("hormones", "Thyroid", "🦋", "Thyroid hormones"),
    ("nutrition", "Nutrition", "🥗", "Vitamins & minerals"),
    ("infection", "Infections", "🛡️", "Inflammation markers"),
]

# code: (name, unit, ref_low, ref_high, ref_text, system, explanation)
CATALOG: dict[str, tuple] = {
    "HBA1C": ("HbA1c (Glycated Haemoglobin)", "%", 4.0, 5.6, "4.0 - 5.6", "sugar",
              "Reflects the average blood sugar over roughly the last 2-3 months."),
    "FBS": ("Fasting Blood Glucose", "mg/dL", 70, 99, "70 - 99", "sugar",
            "Blood sugar measured after not eating for 8-12 hours."),
    "PPBS": ("Post-prandial Blood Glucose", "mg/dL", 70, 140, "70 - 140", "sugar",
             "Blood sugar measured about 2 hours after a meal."),
    "CHOL": ("Total Cholesterol", "mg/dL", None, 200, "< 200", "heart",
             "The total amount of cholesterol carried in the blood."),
    "LDL": ("LDL Cholesterol", "mg/dL", None, 100, "< 100", "heart",
            "Low-density lipoprotein, often called 'bad' cholesterol."),
    "HDL": ("HDL Cholesterol", "mg/dL", 50, None, "> 50", "heart",
            "High-density lipoprotein, often called 'good' cholesterol."),
    "TG": ("Triglycerides", "mg/dL", None, 150, "< 150", "heart", "A type of fat (lipid) found in the blood."),
    "VLDL": ("VLDL Cholesterol", "mg/dL", 5, 30, "5 - 30", "heart", "Very-low-density lipoprotein, which carries triglycerides."),
    "TBIL": ("Serum Bilirubin (Total)", "mg/dL", None, 1.2, "<= 1.2", "liver",
             "A yellow pigment made when red blood cells break down; processed by the liver."),
    "DBIL": ("Serum Bilirubin (Direct)", "mg/dL", None, 0.3, "<= 0.3", "liver", "The part of bilirubin already processed by the liver."),
    "AST": ("Aspartate Aminotransferase (AST/SGOT)", "U/L", None, 40, "< 40", "liver",
            "An enzyme found in the liver and muscles; labs measure it to check liver function."),
    "ALT": ("Alanine Transaminase (ALT/SGPT)", "U/L", None, 40, "< 40", "liver",
            "An enzyme found mostly in the liver; labs measure it to check liver function."),
    "ALP": ("Alkaline Phosphatase (ALP)", "U/L", 40, 129, "40 - 129", "liver", "An enzyme found in the liver and bones."),
    "GGT": ("Gamma Glutamyl Transferase (GGT)", "U/L", None, 60, "< 60", "liver", "A liver enzyme often checked alongside ALP."),
    "ALB": ("Serum Albumin", "g/dL", 3.5, 5.2, "3.5 - 5.2", "liver", "A protein made by the liver."),
    "CREAT": ("Serum Creatinine", "mg/dL", 0.5, 1.1, "0.5 - 1.1", "kidney",
              "A waste product from muscles that the kidneys filter out."),
    "UREA": ("Blood Urea", "mg/dL", 15, 40, "15 - 40", "kidney", "A waste product from protein breakdown, filtered by the kidneys."),
    "URIC": ("Uric Acid", "mg/dL", 2.6, 6.0, "2.6 - 6.0", "kidney", "A waste product from the breakdown of purines in food and cells."),
    "EGFR": ("eGFR", "mL/min/1.73m2", 90, None, "> 90", "kidney", "An estimate of how well the kidneys filter blood."),
    "HB": ("Haemoglobin", "g/dL", 12.0, 15.5, "12.0 - 15.5", "blood", "The protein in red blood cells that carries oxygen."),
    "WBC": ("Total WBC Count", "10^3/uL", 4.0, 11.0, "4.0 - 11.0", "blood", "White blood cells, part of the immune system."),
    "PLT": ("Platelet Count", "10^3/uL", 150, 410, "150 - 410", "blood", "Cell fragments that help blood clot."),
    "RBC": ("RBC Count", "10^6/uL", 3.8, 5.1, "3.8 - 5.1", "blood", "The number of red blood cells."),
    "MCV": ("MCV (Mean Corpuscular Volume)", "fL", 80, 100, "80 - 100", "blood", "The average size of red blood cells."),
    "TSH": ("TSH (Thyroid Stimulating Hormone)", "mIU/L", 0.4, 4.0, "0.4 - 4.0", "hormones",
            "A hormone from the pituitary gland that signals the thyroid."),
    "FT4": ("Free T4", "ng/dL", 0.8, 1.8, "0.8 - 1.8", "hormones", "A thyroid hormone circulating freely in the blood."),
    "FT3": ("Free T3", "pg/mL", 2.3, 4.2, "2.3 - 4.2", "hormones", "The active form of thyroid hormone."),
    "VITD": ("Vitamin D (25-OH)", "ng/mL", 30, 100, "30 - 100", "nutrition", "The main form of vitamin D measured in blood."),
    "B12": ("Vitamin B12", "pg/mL", 200, 900, "200 - 900", "nutrition", "A vitamin needed for nerves and red blood cells."),
    "FERR": ("Ferritin", "ng/mL", 15, 150, "15 - 150", "nutrition", "A protein that stores iron in the body."),
    "CA": ("Serum Calcium", "mg/dL", 8.6, 10.3, "8.6 - 10.3", "nutrition", "The calcium level in the blood."),
    "CRP": ("C-Reactive Protein (CRP)", "mg/L", None, 5, "< 5", "infection",
            "A protein the liver makes in response to inflammation."),
    "ESR": ("ESR (Erythrocyte Sedimentation Rate)", "mm/hr", 0, 20, "0 - 20", "infection",
            "How fast red cells settle in a tube; a general inflammation marker."),
}

ORDER = list(CATALOG)


def system_of(code: str) -> str:
    return CATALOG.get(code, (None,) * 6 + ("",))[5] or "other"


def explain(code: str) -> str:
    return CATALOG.get(code, ("",) * 7)[6]


def flag(code: str, v: float) -> str:
    _, _, lo, hi, *_ = CATALOG[code]
    if lo is not None and v < lo:
        return "L"
    if hi is not None and v > hi:
        return "H"
    return ""


# Synthetic patient history (Sunita Sharma). Keys: report id -> {code: value}
REPORTS = {
    "doc-lab-nov25": {"date": (2025, 11, 12), "lab": "Apex Diagnostics", "values": {
        "HBA1C": 6.9, "FBS": 128, "PPBS": 182, "CHOL": 186, "LDL": 109, "HDL": 48, "TG": 148, "VLDL": 29.6,
        "TBIL": 0.6, "DBIL": 0.2, "AST": 28, "ALT": 36, "ALP": 88, "GGT": 34, "ALB": 4.3,
        "CREAT": 0.8, "UREA": 24, "URIC": 5.4, "EGFR": 96, "HB": 12.6, "WBC": 6.8, "PLT": 248, "RBC": 4.4, "MCV": 86,
        "TSH": 2.2, "FT4": 1.2, "VITD": 16, "B12": 410, "CA": 9.4, "CRP": 2.1, "ESR": 14}},
    "doc-lab-may": {"date": (2026, 5, 9), "lab": "Apex Diagnostics", "values": {
        "HBA1C": 7.2, "FBS": 138, "PPBS": 196, "CHOL": 192, "LDL": 118, "HDL": 46, "TG": 160, "VLDL": 32,
        "TBIL": 0.62, "DBIL": 0.22, "AST": 31, "ALT": 44, "ALP": 92, "GGT": 41, "ALB": 4.2,
        "CREAT": 0.9, "UREA": 27, "URIC": 5.9, "EGFR": 92, "HB": 12.4, "WBC": 7.1, "PLT": 236, "RBC": 4.3, "MCV": 85,
        "TSH": 2.4, "FT4": 1.1, "VITD": 18, "B12": 360, "CA": 9.2, "CRP": 1.8, "ESR": 16}},
    "doc-lab-aug": {"date": (2026, 8, 20), "lab": "City Diagnostics", "values": {"HBA1C": 7.6, "FBS": 150, "PPBS": 208}},
    "doc-lab-nov": {"date": (2026, 11, 18), "lab": "Apex Diagnostics", "values": {
        "HBA1C": 8.1, "FBS": 162, "PPBS": 228, "CHOL": 214, "LDL": 136, "HDL": 44, "TG": 172, "VLDL": 34.4,
        "TBIL": 0.7, "DBIL": 0.24, "AST": 36, "ALT": 52, "ALP": 96, "GGT": 48, "ALB": 4.1,
        "CREAT": 0.9, "UREA": 29, "URIC": 6.3, "EGFR": 91, "HB": 11.8, "WBC": 7.4, "PLT": 241, "RBC": 4.1, "MCV": 83,
        "TSH": 2.6, "FT4": 1.2, "FT3": 3.0, "VITD": 22, "B12": 310, "CA": 9.3, "CRP": 2.4, "ESR": 18}},
}

# For the live upload demo (NOT seeded): a different lab, thyroid + vitamin + CBC panel
UPLOAD_DEMO = {"date": (2026, 2, 14), "lab": "Metro Path Labs", "values": {
    "TSH": 2.3, "FT4": 1.15, "FT3": 3.1, "VITD": 20, "B12": 380, "FERR": 32, "CA": 9.3, "HB": 12.5, "WBC": 6.9,
    "PLT": 244}}
