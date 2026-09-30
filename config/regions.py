# FLOOD-AI
# Andhra Pradesh Hilly & Agency Pilot Regions

AP_HILLY_REGIONS = {

    "Chintoor Agency": {
        "district": "Alluri Sitharama Raju",
        "locations": [
            "Chintoor",
            "Kunavaram",
            "V.R. Puram",
            "Yetapaka"
        ],
        "latitude": 17.7456,
        "longitude": 81.3942,
        "terrain": "Hilly / Agency",
        "hydrology": "Godavari-Sabari valley influence",
        "reason": (
            "Valley and river influence with forested terrain; "
            "selected for terrain-sensitive flash-flood demonstration."
        )
    },

    "Rampachodavaram-Devipatnam": {
        "district": "Alluri Sitharama Raju",
        "locations": [
            "Rampachodavaram",
            "Devipatnam",
            "Maredumilli"
        ],
        "latitude": 17.4209,
        "longitude": 81.8227,
        "terrain": "Hilly / Forest",
        "hydrology": "Godavari catchment influence",
        "reason": (
            "Steep forested catchments and rapid runoff conditions "
            "make this useful for terrain-sensitive risk analysis."
        )
    },

    "Araku-Paderu Agency": {
        "district": "Alluri Sitharama Raju",
        "locations": [
            "Araku Valley",
            "Paderu"
        ],
        "latitude": 18.3234,
        "longitude": 82.8806,
        "terrain": "Highland / Hilly",
        "hydrology": "Mountain drainage",
        "reason": (
            "Higher-elevation terrain and narrow valleys are useful "
            "for demonstrating terrain-controlled runoff."
        )
    },

    "Eluru Upland Agency Fringe": {
        "district": "Eluru",
        "locations": [
            "Polavaram",
            "Velerupadu",
            "Kukunoor"
        ],
        "latitude": 17.5249,
        "longitude": 81.2569,
        "terrain": "Upland / Hilly fringe",
        "hydrology": "Godavari-side drainage",
        "reason": (
            "Selected to demonstrate flood and connectivity "
            "considerations in upland areas."
        )
    },

    "Parvathipuram Manyam Hilly Belt": {
        "district": "Parvathipuram Manyam",
        "locations": [
            "Gummalakshmipuram",
            "Kurupam",
            "Jiyyammavalasa",
            "Salur"
        ],
        "latitude": 18.5177,
        "longitude": 83.2081,
        "terrain": "Hilly / Agency",
        "hydrology": "Nagavali-Suvarnamukhi drainage influence",
        "reason": (
            "Hilly terrain and monsoon drainage conditions make "
            "this a useful pilot zone for terrain-sensitive analysis."
        )
    }
}


def get_region(region_name):
    """
    Return information about a selected AP pilot region.
    """

    return AP_HILLY_REGIONS.get(region_name)


def get_region_names():
    """
    Return available region names.
    """

    return list(AP_HILLY_REGIONS.keys())


if __name__ == "__main__":

    print("=" * 60)
    print("FLOOD-AI AP HILLY / AGENCY PILOT REGIONS")
    print("=" * 60)

    for name, region in AP_HILLY_REGIONS.items():

        print("\n" + name)
        print("-" * len(name))

        print("District :", region["district"])
        print("Locations:", ", ".join(region["locations"]))
        print("Terrain  :", region["terrain"])
        print("Hydrology:", region["hydrology"])