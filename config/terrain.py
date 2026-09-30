import math
import requests


ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"


def get_elevations(points):
    """
    Get elevation values for a list of
    (latitude, longitude) points.
    """

    latitudes = ",".join(str(p[0]) for p in points)
    longitudes = ",".join(str(p[1]) for p in points)

    params = {
        "latitude": latitudes,
        "longitude": longitudes
    }

    response = requests.get(
        ELEVATION_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    return data["elevation"]


def calculate_slope(latitude, longitude):
    """
    Estimate local terrain slope using elevation
    at the center and four nearby points.

    Returns:
        center elevation (m)
        slope (degrees)
    """

    # Small geographic offset around the location.
    # This creates a local terrain sample.
    delta = 0.005

    points = [
        (latitude, longitude),                 # center
        (latitude + delta, longitude),         # north
        (latitude - delta, longitude),         # south
        (latitude, longitude + delta),         # east
        (latitude, longitude - delta),         # west
    ]

    elevations = get_elevations(points)

    center = float(elevations[0])
    north = float(elevations[1])
    south = float(elevations[2])
    east = float(elevations[3])
    west = float(elevations[4])

    # Approximate physical distances.
    lat_distance = 111_000 * delta

    lon_distance = (
        111_000
        * math.cos(math.radians(latitude))
        * delta
    )

    # Elevation gradient in north/south direction.
    dz_dy = (
        (north - south)
        / (2 * lat_distance)
    )

    # Elevation gradient in east/west direction.
    dz_dx = (
        (east - west)
        / (2 * lon_distance)
    )

    # Terrain gradient magnitude.
    gradient = math.sqrt(
        dz_dx ** 2 +
        dz_dy ** 2
    )

    # Convert gradient to slope angle.
    slope_degrees = math.degrees(
        math.atan(gradient)
    )

    return center, slope_degrees


if __name__ == "__main__":

    # Araku Valley pilot location
    latitude = 18.3273
    longitude = 82.8764

    print("=" * 60)
    print("FLOOD-AI TERRAIN / SLOPE TEST")
    print("=" * 60)

    print(
        f"\nLocation: "
        f"{latitude}, {longitude}"
    )

    try:

        elevation, slope = calculate_slope(
            latitude,
            longitude
        )

        print("\nTerrain information")
        print("-" * 30)

        print(
            f"Elevation : "
            f"{elevation:.2f} m"
        )

        print(
            f"Slope     : "
            f"{slope:.2f} degrees"
        )

        print("\nSource:")
        print(
            "Open-Meteo elevation/terrain data "
            "with locally derived slope"
        )

        print(
            "\n✅ TERRAIN ANALYSIS SUCCESSFUL"
        )

    except Exception as e:

        print("\n❌ TERRAIN ANALYSIS ERROR")

        print(type(e).__name__)
        print(str(e))