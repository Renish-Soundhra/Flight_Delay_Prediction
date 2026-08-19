import os
import re
import sys
import urllib.request
import pandas as pd
import numpy as np
from difflib import SequenceMatcher


# =============================================================================
# AIRPORT ID -> IATA MAPPING
# =============================================================================

print("=" * 80)
print("AIRPORT ID -> IATA MAPPING")
print("=" * 80)


# =============================================================================
# PATHS
# =============================================================================

FLIGHTS_PATH = r"D:\Cognizant\flights_clean.csv"
AIRPORTS_PATH = r"C:\Users\ASUS\Downloads\archive (2)\airports.csv"

OUTPUT_PATH = r"D:\Cognizant\airport_id_mapping.csv"

BTS_LOOKUP_PATH = r"D:\Cognizant\L_AIRPORT_ID.csv"


# =============================================================================
# CHECK FILES
# =============================================================================

print("\nChecking local files...")

if not os.path.exists(FLIGHTS_PATH):
    print("ERROR: flights_clean.csv not found")
    print(FLIGHTS_PATH)
    sys.exit(1)

if not os.path.exists(AIRPORTS_PATH):
    print("ERROR: airports.csv not found")
    print(AIRPORTS_PATH)
    sys.exit(1)

print("Flight dataset found. ✓")
print("Airport metadata found. ✓")


# =============================================================================
# LOAD FLIGHTS
# =============================================================================

print("\n" + "=" * 80)
print("LOADING FLIGHT DATA")
print("=" * 80)

flights = pd.read_csv(
    FLIGHTS_PATH,
    usecols=[
        "ORIGIN_AIRPORT",
        "DESTINATION_AIRPORT"
    ],
    dtype=str
)

print("Flight rows:", len(flights))


# =============================================================================
# CLEAN AIRPORT IDENTIFIERS
# =============================================================================

flights["ORIGIN_AIRPORT"] = (
    flights["ORIGIN_AIRPORT"]
    .astype(str)
    .str.strip()
    .str.upper()
)

flights["DESTINATION_AIRPORT"] = (
    flights["DESTINATION_AIRPORT"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# =============================================================================
# FIND NUMERIC AIRPORT IDS
# =============================================================================

origin_values = set(
    flights["ORIGIN_AIRPORT"].dropna()
)

destination_values = set(
    flights["DESTINATION_AIRPORT"].dropna()
)

all_values = (
    origin_values |
    destination_values
)

numeric_ids = sorted(
    [
        x for x in all_values
        if re.fullmatch(r"\d+", x)
    ],
    key=lambda x: int(x)
)

iata_codes = sorted(
    [
        x for x in all_values
        if re.fullmatch(r"[A-Z]{3}", x)
    ]
)

print("\n" + "=" * 80)
print("IDENTIFIER SUMMARY")
print("=" * 80)

print("Total unique identifiers :", len(all_values))
print("Numeric BTS airport IDs  :", len(numeric_ids))
print("IATA airport codes       :", len(iata_codes))

print("\nNumeric IDs:")
print(numeric_ids[:30])

print("\nIATA codes:")
print(iata_codes[:30])


# =============================================================================
# LOAD AIRPORT METADATA
# =============================================================================

print("\n" + "=" * 80)
print("LOADING AIRPORT METADATA")
print("=" * 80)

airports = pd.read_csv(
    AIRPORTS_PATH,
    low_memory=False
)

print("Airport rows:", len(airports))
print("Airport columns:", len(airports.columns))


required_columns = [
    "IATA_CODE",
    "AIRPORT",
    "CITY",
    "STATE",
    "COUNTRY",
    "LATITUDE",
    "LONGITUDE"
]

missing = [
    c for c in required_columns
    if c not in airports.columns
]

if missing:
    print("\nERROR: Missing columns:")
    print(missing)
    sys.exit(1)


# =============================================================================
# CLEAN AIRPORT METADATA
# =============================================================================

for col in [
    "IATA_CODE",
    "AIRPORT",
    "CITY",
    "STATE",
    "COUNTRY"
]:

    airports[col] = (
        airports[col]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )


# =============================================================================
# DOWNLOAD BTS AIRPORT ID LOOKUP
# =============================================================================

print("\n" + "=" * 80)
print("BTS AIRPORT ID LOOKUP")
print("=" * 80)


BTS_URL = (
    "https://raw.githubusercontent.com/"
    "dannguyen/bts-transstats-t100-domestic-demo/"
    "master/data/lookup-tables/L_AIRPORT_ID.csv"
)


if not os.path.exists(BTS_LOOKUP_PATH):

    print("\nDownloading BTS airport lookup...")

    try:

        urllib.request.urlretrieve(
            BTS_URL,
            BTS_LOOKUP_PATH
        )

        print(
            "Downloaded successfully. ✓"
        )

    except Exception as e:

        print("\nERROR downloading BTS lookup:")
        print(e)

        print("\nYou can manually download:")
        print(BTS_URL)

        sys.exit(1)

else:

    print(
        "Existing BTS lookup found. ✓"
    )


# =============================================================================
# LOAD BTS LOOKUP
# =============================================================================

print("\nLoading BTS lookup...")

bts = pd.read_csv(
    BTS_LOOKUP_PATH,
    header=None,
    names=[
        "AIRPORT_ID",
        "DESCRIPTION"
    ],
    dtype=str
)

print(
    "BTS lookup rows:",
    len(bts)
)


# =============================================================================
# CLEAN BTS LOOKUP
# =============================================================================

bts["AIRPORT_ID"] = (
    bts["AIRPORT_ID"]
    .astype(str)
    .str.strip()
    .str.replace(
        '"',
        "",
        regex=False
    )
)

bts["DESCRIPTION"] = (
    bts["DESCRIPTION"]
    .astype(str)
    .str.strip()
    .str.replace(
        '"',
        "",
        regex=False
    )
)


# =============================================================================
# KEEP ONLY OUR 307 IDS
# =============================================================================

bts = bts[
    bts["AIRPORT_ID"].isin(
        numeric_ids
    )
].copy()

print(
    "\nBTS IDs matching our flight dataset:",
    len(bts)
)


# =============================================================================
# PARSE BTS DESCRIPTION
# =============================================================================
#
# Typical:
#
# 10397 -> Atlanta, GA: Hartsfield-Jackson Atlanta International
#
# We extract:
#
# city
# state
# airport name
#
# =============================================================================


def parse_description(description):

    description = str(
        description
    ).strip()

    if ":" in description:

        location, airport_name = (
            description.split(
                ":",
                1
            )
        )

    else:

        location = description
        airport_name = ""

    location = location.strip()
    airport_name = airport_name.strip()

    city = ""
    state = ""

    if "," in location:

        city, state = (
            location.rsplit(
                ",",
                1
            )
        )

        city = city.strip()
        state = state.strip()

    else:

        city = location

    return (
        city.upper(),
        state.upper(),
        airport_name.upper()
    )


parsed = bts[
    "DESCRIPTION"
].apply(
    parse_description
)

bts[
    [
        "BTS_CITY",
        "BTS_STATE",
        "BTS_AIRPORT_NAME"
    ]
] = pd.DataFrame(
    parsed.tolist(),
    index=bts.index
)


# =============================================================================
# TEXT NORMALIZATION
# =============================================================================


def normalize_text(value):

    value = str(value).upper()

    value = (
        value
        .replace(
            "INTERNATIONAL",
            ""
        )
        .replace(
            "AIRPORT",
            ""
        )
        .replace(
            "REGIONAL",
            ""
        )
        .replace(
            "MUNICIPAL",
            ""
        )
        .replace(
            "FIELD",
            ""
        )
        .replace(
            "COUNTY",
            ""
        )
    )

    value = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# Create normalized fields

for col in [
    "CITY",
    "STATE",
    "AIRPORT"
]:

    airports[
        f"_NORM_{col}"
    ] = airports[col].apply(
        normalize_text
    )


for col in [
    "BTS_CITY",
    "BTS_STATE",
    "BTS_AIRPORT_NAME"
]:

    bts[
        f"_NORM_{col}"
    ] = bts[col].apply(
        normalize_text
    )


# =============================================================================
# MATCH FUNCTION
# =============================================================================


def similarity(a, b):

    if not a or not b:
        return 0.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def find_best_airport(
    bts_row,
    airport_table
):

    bts_city = bts_row["_NORM_BTS_CITY"]
    bts_state = bts_row["_NORM_BTS_STATE"]
    bts_name = bts_row["_NORM_BTS_AIRPORT_NAME"]

    # ---------------------------------------------------------
    # First filter by state
    # ---------------------------------------------------------

    candidates = airport_table[
        airport_table["_NORM_STATE"]
        ==
        bts_state
    ]

    # If no state match, use entire table
    if len(candidates) == 0:

        candidates = airport_table

    best_score = -1
    best_row = None

    for idx, row in candidates.iterrows():

        city_score = similarity(
            bts_city,
            row["_NORM_CITY"]
        )

        name_score = similarity(
            bts_name,
            row["_NORM_AIRPORT"]
        )

        # City is more important than airport-name wording
        score = (
            0.60 * city_score
            +
            0.40 * name_score
        )

        # Strong bonus for exact city
        if (
            bts_city
            ==
            row["_NORM_CITY"]
        ):

            score += 0.25

        if score > best_score:

            best_score = score
            best_row = row

    return (
        best_row,
        best_score
    )


# =============================================================================
# BUILD MAPPING
# =============================================================================

print("\n" + "=" * 80)
print("MATCHING BTS IDS TO AIRPORT METADATA")
print("=" * 80)

results = []

total = len(bts)

for counter, (_, row) in enumerate(
    bts.iterrows(),
    start=1
):

    best_row, score = (
        find_best_airport(
            row,
            airports
        )
    )

    if best_row is None:

        results.append({
            "AIRPORT_ID":
                row["AIRPORT_ID"],

            "BTS_DESCRIPTION":
                row["DESCRIPTION"],

            "IATA_CODE":
                "",

            "CITY":
                "",

            "STATE":
                "",

            "AIRPORT":
                "",

            "LATITUDE":
                np.nan,

            "LONGITUDE":
                np.nan,

            "MATCH_SCORE":
                0.0
        })

    else:

        results.append({
            "AIRPORT_ID":
                row["AIRPORT_ID"],

            "BTS_DESCRIPTION":
                row["DESCRIPTION"],

            "IATA_CODE":
                best_row["IATA_CODE"],

            "CITY":
                best_row["CITY"],

            "STATE":
                best_row["STATE"],

            "AIRPORT":
                best_row["AIRPORT"],

            "LATITUDE":
                best_row["LATITUDE"],

            "LONGITUDE":
                best_row["LONGITUDE"],

            "MATCH_SCORE":
                score
        })

    if (
        counter % 25 == 0
        or counter == total
    ):

        print(
            f"Processed {counter}/{total}"
        )


mapping = pd.DataFrame(
    results
)


# =============================================================================
# VALIDATION
# =============================================================================

print("\n" + "=" * 80)
print("MAPPING VALIDATION")
print("=" * 80)


print(
    "\nTotal numeric IDs required:",
    len(numeric_ids)
)

print(
    "BTS IDs found:",
    len(bts)
)

print(
    "Mappings generated:",
    len(mapping)
)


# =============================================================================
# SCORE DISTRIBUTION
# =============================================================================

print("\nMatch score distribution:")

print(
    mapping[
        "MATCH_SCORE"
    ].describe()
)


# =============================================================================
# LOW CONFIDENCE
# =============================================================================

LOW_CONFIDENCE = 0.70

low_confidence = mapping[
    mapping["MATCH_SCORE"]
    <
    LOW_CONFIDENCE
].copy()


print(
    "\nLow-confidence mappings:",
    len(low_confidence)
)


if len(low_confidence) > 0:

    print(
        "\nLOW-CONFIDENCE MAPPINGS:"
    )

    print(
        low_confidence[
            [
                "AIRPORT_ID",
                "BTS_DESCRIPTION",
                "IATA_CODE",
                "CITY",
                "STATE",
                "MATCH_SCORE"
            ]
        ]
        .sort_values(
            "MATCH_SCORE"
        )
        .to_string(
            index=False
        )
    )


# =============================================================================
# MANUAL KNOWN-MAPPING VALIDATION
# =============================================================================

print("\n" + "=" * 80)
print("KNOWN BTS MAPPING VALIDATION")
print("=" * 80)


known_mappings = {
    "10397": "ATL",
    "12892": "LAX",
    "11292": "DEN",
    "11298": "DFW",
    "13930": "ORD",
    "14771": "SFO",
    "12266": "IAH",
    "12478": "JFK",
    "12889": "LAS",
    "13487": "MSP"
}


known_failed = []

for airport_id, expected_iata in (
    known_mappings.items()
):

    row = mapping[
        mapping["AIRPORT_ID"]
        ==
        airport_id
    ]

    if len(row) == 0:

        print(
            f"{airport_id} -> NOT FOUND"
        )

        known_failed.append(
            airport_id
        )

        continue

    actual = row.iloc[0][
        "IATA_CODE"
    ]

    print(
        f"{airport_id} -> "
        f"{actual} "
        f"(expected {expected_iata})"
    )

    if actual != expected_iata:

        known_failed.append(
            airport_id
        )


# =============================================================================
# CHECK ALL REQUIRED IDS
# =============================================================================

mapped_ids = set(
    mapping[
        "AIRPORT_ID"
    ].astype(str)
)

missing_ids = [
    x
    for x in numeric_ids
    if x not in mapped_ids
]


print("\n" + "=" * 80)
print("FINAL VALIDATION")
print("=" * 80)

print(
    "Required numeric IDs :",
    len(numeric_ids)
)

print(
    "Mapped numeric IDs   :",
    len(mapped_ids)
)

print(
    "Missing numeric IDs  :",
    len(missing_ids)
)

print(
    "Known mapping errors :",
    len(known_failed)
)


if missing_ids:

    print(
        "\nMissing IDs:"
    )

    for x in missing_ids:
        print(
            " ",
            x
        )


# =============================================================================
# SAVE MAPPING
# =============================================================================

print("\n" + "=" * 80)
print("SAVING MAPPING")
print("=" * 80)


mapping.to_csv(
    OUTPUT_PATH,
    index=False
)

print(
    "\nMapping saved to:"
)

print(
    OUTPUT_PATH
)


# =============================================================================
# FINAL DECISION
# =============================================================================

print("\n" + "=" * 80)
print("MAPPING STATUS")
print("=" * 80)


if (
    len(missing_ids) == 0
    and
    len(known_failed) == 0
    and
    len(low_confidence) == 0
):

    print(
        "\n✓✓✓ MAPPING PASSED ✓✓✓"
    )

    print(
        "\nAll numeric airport IDs were mapped "
        "with acceptable confidence."
    )

    print(
        "\nYou can now use:"
    )

    print(
        OUTPUT_PATH
    )

else:

    print(
        "\n⚠ MAPPING NEEDS REVIEW"
    )

    print(
        "\nDO NOT run the expensive Step 14 "
        "feature engineering yet."
    )

    print(
        "\nReview the low-confidence/missing "
        "mappings above first."
    )


# =============================================================================
# SAMPLE
# =============================================================================

print("\n" + "=" * 80)
print("SAMPLE MAPPING")
print("=" * 80)

print(
    mapping[
        [
            "AIRPORT_ID",
            "IATA_CODE",
            "CITY",
            "STATE",
            "AIRPORT",
            "MATCH_SCORE"
        ]
    ]
    .head(30)
    .to_string(
        index=False
    )
)


print("\n" + "=" * 80)
print("SCRIPT COMPLETE")
print("=" * 80)