import pandas as pd
import os

# ============================================================
# PATHS
# ============================================================

MAPPING_PATH = r"D:\Cognizant\airport_id_mapping.csv"
OUTPUT_PATH = r"D:\Cognizant\airport_id_mapping_final.csv"

# ============================================================
# LOAD CURRENT MAPPING
# ============================================================

print("=" * 80)
print("FIXING AIRPORT ID -> IATA MAPPING")
print("=" * 80)

df = pd.read_csv(
    MAPPING_PATH,
    dtype=str
)

print("\nCurrent mappings:", len(df))

# ============================================================
# VERIFIED CORRECTIONS
# ============================================================

corrections = {
    "11193": "CVG",
    "10529": "BDL",
    "13256": "MFE",
    "15323": "TRI",
    "14252": "PSC",
    "11617": "EWN",
    "12448": "JAN",
    "15041": "SUN",
    "12264": "IAD",
    "12007": "GTR",
    "12016": "GUM",
    "13184": "MBS",
    "10685": "BMI",
    "14489": "RDM"
}

# ============================================================
# APPLY CORRECTIONS
# ============================================================

print("\nApplying corrections...")

for airport_id, correct_iata in corrections.items():

    mask = (
        df["AIRPORT_ID"].astype(str)
        == airport_id
    )

    if mask.sum() == 0:

        print(
            f"WARNING: {airport_id} not found"
        )

        continue

    old_iata = df.loc[
        mask,
        "IATA_CODE"
    ].iloc[0]

    df.loc[
        mask,
        "IATA_CODE"
    ] = correct_iata

    print(
        f"{airport_id}: "
        f"{old_iata} -> {correct_iata}"
    )


# ============================================================
# VALIDATE
# ============================================================

print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

print(
    "\nTotal mappings:",
    len(df)
)

print(
    "Unique airport IDs:",
    df["AIRPORT_ID"].nunique()
)

print(
    "Unique IATA codes:",
    df["IATA_CODE"].nunique()
)

# ============================================================
# CHECK REQUIRED CORRECTIONS
# ============================================================

print("\nCorrected mappings:")

for airport_id, expected_iata in corrections.items():

    row = df[
        df["AIRPORT_ID"].astype(str)
        == airport_id
    ]

    if len(row) == 0:

        print(
            f"❌ {airport_id} missing"
        )

        continue

    actual = row.iloc[0]["IATA_CODE"]

    if actual == expected_iata:

        print(
            f"✓ {airport_id} -> {actual}"
        )

    else:

        print(
            f"❌ {airport_id} -> {actual} "
            f"(expected {expected_iata})"
        )


# ============================================================
# REMOVE OLD FUZZY SCORE
# ============================================================

if "MATCH_SCORE" in df.columns:

    df.drop(
        columns=["MATCH_SCORE"],
        inplace=True
    )


# ============================================================
# SAVE FINAL MAPPING
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n" + "=" * 80)
print("FINAL MAPPING SAVED")
print("=" * 80)

print(
    "\nFile:"
)

print(
    OUTPUT_PATH
)

print(
    "\n✓ Airport mapping finalized."
)