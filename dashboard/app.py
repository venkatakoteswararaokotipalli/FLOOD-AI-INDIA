import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd

try:
    from twilio.rest import Client
except ImportError:
    Client = None
import folium
from streamlit_folium import st_folium

from config.regions import AP_HILLY_REGIONS
from utils.live_predictor import predict_live_risk
from utils.satellite_rainfall import get_satellite_rainfall
from utils.data_fusion import assess_rainfall_sources
from utils.river_data import get_river_level
from utils.alert_engine import build_alert

# New: Vijayawada / Budameru / Krishna case-study locations
try:
    from case_study_locations import CASE_STUDY_LOCATIONS
except ImportError:
    CASE_STUDY_LOCATIONS = {}


st.set_page_config(
    page_title="FLOOD-AI INDIA",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 FLOOD-AI INDIA")
st.subheader("Multi-Source Flash Flood Prediction & Risk Intelligence")
st.caption(
    "India-wide scalable architecture • Andhra Pradesh "
    "hilly/agency pilot implementation"
)
st.divider()


# =========================================================
# LOCATION CONTROL
# =========================================================

st.sidebar.title("📍 Location Control")

region_name = st.sidebar.selectbox(
    "Select AP Pilot Region",
    list(AP_HILLY_REGIONS.keys())
)

region = AP_HILLY_REGIONS[region_name]

location_name = st.sidebar.selectbox(
    "Select Location",
    region["locations"]
)

st.sidebar.markdown("### 🏔️ Terrain Profile")
st.sidebar.write(f"**Terrain:** {region['terrain']}")
st.sidebar.write(f"**Hydrology:** {region['hydrology']}")
st.sidebar.info(region["reason"])

latitude = region["latitude"]
longitude = region["longitude"]


# =========================================================
# RIVER / HYDROLOGY
# =========================================================

river_observation = get_river_level(latitude, longitude)
river_level = river_observation.get("water_level_m")

if river_level is None:
    river_level = 4.0
    river_fallback = True
else:
    river_level = float(river_level)
    river_fallback = False

st.sidebar.markdown("### 🌊 River / Hydrology")

st.sidebar.metric(
    "River Level",
    f"{river_level:.2f} m"
)

st.sidebar.write(
    f"**River:** {river_observation.get('river_name', 'Not loaded')}"
)

st.sidebar.caption(
    f"Source: {river_observation.get('source', 'River layer')} • "
    f"Status: {river_observation.get('status', 'UNKNOWN')}"
)

if river_fallback:
    st.sidebar.warning(
        "River dataset unavailable. Demo fallback value is being used."
    )
else:
    st.sidebar.info(
        "Current hackathon value is from the project's demo river-level CSV. "
        "Operational deployment requires verified CWC/telemetry data."
    )


# =========================================================
# RUN ANALYSIS
# =========================================================

run_analysis = st.sidebar.button(
    "🔍 RUN FLOOD ANALYSIS",
    type="primary",
    use_container_width=True
)

if "analysis" not in st.session_state:
    st.session_state.analysis = None


if run_analysis:

    with st.spinner(
        "Collecting environmental data and running AI model..."
    ):

        try:

            result = predict_live_risk(
                latitude=latitude,
                longitude=longitude,
                river_level_m=river_level
            )

            satellite = get_satellite_rainfall(
                latitude,
                longitude
            )

            weather_rainfall = result["weather"]["rainfall_mm"]

            # =================================================
            # DEMO RAINFALL SCENARIO
            # =================================================

            st.sidebar.markdown("### 🌧️ Rainfall Scenario")

            use_demo_rainfall = st.sidebar.checkbox(
                "Enable Demo Rainfall",
                value=False
            )

            if use_demo_rainfall:

                demo_rainfall = st.sidebar.slider(
                    "Demo Rainfall (mm)",
                    min_value=0.0,
                    max_value=200.0,
                    value=50.0,
                    step=5.0
                )

                rainfall_for_display = demo_rainfall

            else:

                rainfall_for_display = weather_rainfall

            satellite_value = satellite.get("rainfall_mm")

            fusion = assess_rainfall_sources(
                weather_rainfall=rainfall_for_display,
                satellite_rainfall=satellite_value
            )

            result["satellite_rainfall"] = satellite
            result["rainfall_fusion"] = fusion
            result["river_observation"] = river_observation

            result["demo_rainfall_enabled"] = use_demo_rainfall
            result["rainfall_for_display"] = rainfall_for_display

            st.session_state.analysis = result

        except Exception as e:

            st.error(
                f"Analysis failed: {type(e).__name__}: {str(e)}"
            )


# =========================================================
# WAITING SCREEN
# =========================================================

if st.session_state.analysis is None:

    st.info(
        "👈 Select a pilot region and location, "
        "then click **RUN FLOOD ANALYSIS**."
    )

    st.markdown(
        "## 🏔️ Selected High-Risk Hilly & Agency Pilot Areas"
    )

    table_data = []

    for name, data in AP_HILLY_REGIONS.items():

        table_data.append({
            "Pilot Zone": name,
            "District": data["district"],
            "Locations": ", ".join(data["locations"]),
            "Terrain": data["terrain"]
        })

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Why hilly regions?")

    st.write(
        "Hilly and agency regions are useful for demonstrating "
        "terrain-sensitive flash-flood analysis because elevation "
        "and slope influence runoff behaviour. FLOOD-AI combines "
        "these terrain indicators with rainfall, soil moisture "
        "and hydrological information."
    )

    st.warning(
        "Prototype note: the current ML model uses synthetic/demo "
        "training data and is not an operational emergency warning service."
    )

    st.stop()


# =========================================================
# ANALYSIS RESULT
# =========================================================

result = st.session_state.analysis

weather = result["weather"]
probability = result["probability"]
risk_level = result["risk_level"]

elevation = result["elevation_m"]
slope = result["slope_degree"]


# =========================================================
# SATELLITE DATA
# =========================================================

satellite = result.get(
    "satellite_rainfall",
    {
        "rainfall_mm": None,
        "source": "MOSDAC GSMaP_ISRO",
        "status": "NOT LOADED",
        "message": "Satellite rainfall data unavailable."
    }
)

satellite_rainfall = satellite.get("rainfall_mm")
satellite_status = satellite.get("status", "UNKNOWN")


# =========================================================
# RIVER DATA
# =========================================================

river_observation = result.get(
    "river_observation",
    river_observation
)

river_name = river_observation.get(
    "river_name",
    "Not loaded"
)

river_status = river_observation.get(
    "status",
    "UNKNOWN"
)

river_source = river_observation.get(
    "source",
    "River layer"
)

river_latitude = river_observation.get(
    "latitude",
    latitude
)

river_longitude = river_observation.get(
    "longitude",
    longitude
)


# =========================================================
# RAINFALL DISPLAY VALUE
# =========================================================

demo_rainfall_enabled = result.get(
    "demo_rainfall_enabled",
    False
)

rainfall_for_display = result.get(
    "rainfall_for_display",
    weather["rainfall_mm"]
)


# =========================================================
# RAINFALL FUSION
# =========================================================

fusion = result.get(
    "rainfall_fusion",
    {
        "status": "UNKNOWN",
        "label": "Assessment unavailable",
        "message": "Rainfall source assessment unavailable.",
        "difference_mm": None,
        "difference_percent": None
    }
)

fusion_status = fusion.get(
    "status",
    "UNKNOWN"
)

fusion_label = fusion.get(
    "label",
    "Assessment unavailable"
)

fusion_message = fusion.get(
    "message",
    ""
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    f"## 📍 {location_name}"
)

st.caption(
    f"{region_name} • {region['district']} • {region['terrain']}"
)


# =========================================================
# TOP METRICS
# =========================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    if demo_rainfall_enabled:

        st.metric(
            "🌧️ Demo Rainfall",
            f"{rainfall_for_display:.2f} mm"
        )

    else:

        st.metric(
            "🌧️ Weather Rainfall",
            f"{weather['rainfall_mm']:.2f} mm"
        )


with c2:

    st.metric(
        "💧 Soil Moisture",
        f"{weather['soil_moisture_percent']:.1f}%"
    )


with c3:

    st.metric(
        "⛰️ Elevation",
        f"{elevation:.1f} m"
    )


with c4:

    st.metric(
        "📐 Slope",
        f"{slope:.2f}°"
    )


st.divider()


# =========================================================
# AI RISK + ENVIRONMENTAL INTELLIGENCE
# =========================================================

risk_col, data_col = st.columns([1, 2])

with risk_col:

    st.subheader("🤖 AI Flood Risk")

    st.metric(
        "Model Flood-Class Score",
        f"{probability:.2f}%"
    )

    if risk_level == "CRITICAL":

        st.error(
            f"🚨 {risk_level} RISK"
        )

    elif risk_level == "HIGH":

        st.warning(
            f"⚠️ {risk_level} RISK"
        )

    elif risk_level == "MODERATE":

        st.warning(
            f"🟠 {risk_level} RISK"
        )

    else:

        st.success(
            f"🟢 {risk_level} RISK"
        )


with data_col:

    st.subheader("📡 Environmental Intelligence")

    environmental_data = pd.DataFrame({

        "Parameter": [
            "Weather-model Rainfall",
            "Satellite Rainfall",
            "Temperature",
            "Humidity",
            "Soil Moisture",
            "Elevation",
            "Slope",
            "River Level"
        ],

        "Value": [

            (
                f"{rainfall_for_display:.2f} mm"
                if demo_rainfall_enabled
                else f"{weather['rainfall_mm']:.2f} mm"
            ),

            (
                f"{satellite_rainfall:.2f} mm"
                if satellite_rainfall is not None
                else "Not available"
            ),

            f"{weather['temperature_c']:.2f} °C",

            f"{weather['humidity_percent']:.2f} %",

            f"{weather['soil_moisture_percent']:.2f} %",

            f"{elevation:.2f} m",

            f"{slope:.2f}°",

            f"{river_name}: {river_level:.2f} m"
        ]
    })

    st.dataframe(
        environmental_data,
        use_container_width=True,
        hide_index=True
    )


st.divider()


# =========================================================
# MULTI-SOURCE STATUS
# =========================================================

st.subheader("📡 Multi-Source Data Status")

source1, source2, source3, source4, source5 = st.columns(5)

with source1:

    st.success(
        "🌦️ Weather Model\n\nLIVE"
    )

with source2:

    if satellite_status == "AVAILABLE":

        st.info(
            "🛰️ GSMaP Satellite\n\nDEMO / READY"
        )

    else:

        st.warning(
            "🛰️ GSMaP Satellite\n\n"
            f"{satellite_status}"
        )

with source3:

    st.success(
        "⛰️ Elevation\n\nLIVE"
    )

with source4:

    st.success(
        "📐 Slope\n\nDERIVED"
    )

with source5:

    if river_status == "DEMO":

        st.warning(
            "🌊 River Layer\n\nDEMO / READY"
        )

    elif river_status == "AVAILABLE":

        st.success(
            "🌊 River Layer\n\nLIVE / READY"
        )

    else:

        st.warning(
            f"🌊 River Layer\n\n{river_status}"
        )


# =========================================================
# RIVER LAYER
# =========================================================

st.markdown("### 🌊 River / Hydrology Layer")

if river_status in ["DEMO", "AVAILABLE"]:

    st.success(
        f"{river_name} water level loaded: "
        f"**{river_level:.2f} m**"
    )

else:

    st.warning(
        f"River level fallback in use: "
        f"**{river_level:.2f} m**"
    )

st.caption(
    f"Source: {river_source}. Current status: {river_status}. "
    "The present hackathon dataset contains demonstration values; "
    "verified CWC/telemetry observations are required for operational deployment."
)


# =========================================================
# SATELLITE RAINFALL
# =========================================================

st.markdown("### 🛰️ Satellite Rainfall Layer")

if satellite_rainfall is not None:

    st.success(
        f"GSMaP rainfall value loaded: "
        f"**{satellite_rainfall:.2f} mm**"
    )

    st.caption(
        "Current value comes from the project's demo/test "
        "satellite_rainfall.csv. The integration layer is "
        "designed to accept MOSDAC GSMaP_ISRO data."
    )

else:

    st.warning(
        "GSMaP satellite rainfall data is not currently loaded."
    )

    st.caption(
        satellite.get(
            "message",
            "Satellite rainfall unavailable."
        )
    )


# =========================================================
# MULTI-SOURCE RAINFALL ASSESSMENT
# =========================================================

st.markdown("### 🔄 Multi-Source Rainfall Assessment")

if fusion_status == "CORROBORATED":

    st.success(
        f"✅ {fusion_label}"
    )

elif fusion_status == "SATELLITE_SIGNAL":

    st.warning(
        f"🛰️ {fusion_label}"
    )

elif fusion_status == "WEATHER_SIGNAL":

    st.warning(
        f"🌦️ {fusion_label}"
    )

elif fusion_status == "SOURCE_DIVERGENCE":

    st.warning(
        f"⚠️ {fusion_label}"
    )

elif fusion_status == "WEATHER_ONLY":

    st.info(
        f"ℹ️ {fusion_label}"
    )

else:

    st.info(
        f"ℹ️ {fusion_label}"
    )

st.write(fusion_message)

if fusion.get("difference_mm") is not None:

    st.caption(
        f"Source difference: "
        f"{fusion['difference_mm']:.2f} mm "
        f"({fusion['difference_percent']:.1f}%)"
    )

if demo_rainfall_enabled:

    st.info(
        "🧪 Demo mode: the rainfall value shown above is a "
        "controlled demonstration scenario. It is not a live "
        "weather observation and does not replace the trained "
        "Random Forest input."
    )

else:

    st.info(
        "ℹ️ Model note: the current Random Forest prediction "
        "continues to use the existing weather-model rainfall "
        "feature. The satellite rainfall layer is currently "
        "integrated for multi-source observation and validation. "
        "Satellite-data fusion into the trained ML features "
        "requires appropriate historical training data."
    )


st.divider()


# =========================================================
# GIS MAP
# =========================================================

st.subheader("🗺️ GIS Risk Map")

map_object = folium.Map(
    location=[latitude, longitude],
    zoom_start=10,
    tiles="OpenStreetMap"
)

if risk_level == "CRITICAL":

    marker_color = "red"

elif risk_level == "HIGH":

    marker_color = "orange"

elif risk_level == "MODERATE":

    marker_color = "blue"

else:

    marker_color = "green"


if satellite_rainfall is not None:

    popup_text = (
        f"<b>{location_name}</b><br>"
        f"Risk: {risk_level}<br>"
        f"Model score: {probability:.2f}%<br>"
        f"Rainfall Used for Assessment: "
        f"{rainfall_for_display:.2f} mm<br>"
        f"Satellite Rainfall: {satellite_rainfall:.2f} mm<br>"
        f"River: {river_name}<br>"
        f"River Level: {river_level:.2f} m"
    )

else:

    popup_text = (
        f"<b>{location_name}</b><br>"
        f"Risk: {risk_level}<br>"
        f"Model score: {probability:.2f}%<br>"
        f"Rainfall Used for Assessment: "
        f"{rainfall_for_display:.2f} mm<br>"
        f"Satellite Rainfall: Not available<br>"
        f"River: {river_name}<br>"
        f"River Level: {river_level:.2f} m"
    )


folium.Marker(
    location=[latitude, longitude],
    popup=popup_text,
    tooltip=f"⚠️ {location_name} • {risk_level} RISK",
    icon=folium.Icon(
        color=marker_color,
        icon="warning-sign"
    )
).add_to(map_object)


# =========================================================
# VIJAYAWADA / BUDAMERU / KRISHNA CASE-STUDY LOCATIONS
# =========================================================

for case_name, case in CASE_STUDY_LOCATIONS.items():

    if case_name == location_name:
        continue

    folium.CircleMarker(
        location=[
            case["latitude"],
            case["longitude"]
        ],
        radius=5,
        tooltip=f"{case_name} • {case['system']}",
        popup=(
            f"<b>{case_name}</b><br>"
            f"System: {case['system']}<br>"
            f"Note: {case['note']}<br>"
            f"Latitude: {case['latitude']}<br>"
            f"Longitude: {case['longitude']}"
        ),
        color="blue",
        fill=True,
        fill_opacity=0.7
    ).add_to(map_object)


folium.Circle(
    location=[latitude, longitude],
    radius=5000,
    popup="AI flood-risk monitoring zone",
    tooltip="AI monitoring zone",
    color=marker_color,
    fill=True,
    fill_opacity=0.15
).add_to(map_object)


folium.Marker(
    location=[river_latitude, river_longitude],
    popup=(
        f"<b>🌊 {river_name}</b><br>"
        f"Water level: {river_level:.2f} m<br>"
        f"Status: {river_status}<br>"
        f"Source: {river_source}"
    ),
    tooltip=(
        f"🌊 {river_name} • "
        f"{river_level:.2f} m"
    ),
    icon=folium.Icon(
        color="blue",
        icon="tint"
    )
).add_to(map_object)


if (
    river_latitude,
    river_longitude
) != (
    latitude,
    longitude
):

    folium.PolyLine(
        locations=[
            [latitude, longitude],
            [river_latitude, river_longitude]
        ],
        tooltip="Monitoring location ↔ river observation",
        weight=1.5,
        dash_array="4, 8",
        opacity=0.6
    ).add_to(map_object)


folium.LayerControl().add_to(map_object)

st_folium(
    map_object,
    width=None,
    height=500
)


st.divider()


# =========================================================
# AI RISK EXPLANATION
# =========================================================

st.subheader("🧠 AI Risk Explanation")

factors = []

if weather["rainfall_mm"] > 20:

    factors.append(
        "🌧️ Elevated weather-model rainfall detected"
    )

if satellite_rainfall is not None and satellite_rainfall > 20:

    factors.append(
        "🛰️ Elevated satellite rainfall value detected"
    )

if weather["soil_moisture_percent"] > 60:

    factors.append(
        "💧 High soil moisture indicates wet ground conditions"
    )

if slope > 10:

    factors.append(
        "📐 Steep terrain may increase runoff response"
    )

if elevation < 200:

    factors.append(
        "⛰️ Relatively low elevation may increase local flood exposure"
    )

if river_level > 5:

    factors.append(
        "🌊 Elevated river-level input"
    )

if not factors:

    factors.append(
        "No major threshold-based contributing factor detected "
        "in the current demonstration inputs."
    )

for factor in factors:

    st.write(factor)


st.divider()


# =========================================================
# TWILIO SMS HELPER
# =========================================================

def send_flood_sms(location_name, region_name, risk_level, probability,
                   river_name, river_level):
    if Client is None:
        return False, "Twilio package is not installed. Run: pip install twilio"

    try:
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        from_number = st.secrets["TWILIO_FROM_NUMBER"]
        to_number = st.secrets["TWILIO_TO_NUMBER"]
    except Exception:
        return False, (
            "Twilio secrets are missing. Add TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER and TWILIO_TO_NUMBER "
            "to Streamlit secrets."
        )

    # Send a normal SMS body. Do not use a template name as the body.
    # Twilio trial accounts may still require the destination number
    # to be verified in the Twilio console.
    body = (
        f"FLOOD-AI INDIA ALERT\\n"
        f"Location: {location_name}\\n"
        f"Region: {region_name}\\n"
        f"Risk: {risk_level}\\n"
        f"Model score: {float(probability):.1f}%\\n"
        f"River: {river_name}\\n"
        f"River level: {float(river_level):.2f} m\\n"
        f"Please follow official emergency instructions."
    )

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        return True, f"SMS sent successfully. Message SID: {message.sid}"
    except Exception as e:
        return False, (
            f"SMS sending failed: {type(e).__name__}: {e}"
        )


# =========================================================
# ALERT & EMERGENCY RESPONSE
# =========================================================

st.subheader("🚨 Alert & Emergency Response")

st.info(
    "Demo SMS mode: any model risk level, including LOW, can trigger "
    "an SMS to the verified Twilio recipient."
)

demo_mode = st.checkbox("🧪 Enable Alert Demo", value=True)

if demo_mode:
    demo_probability = float(probability)
    demo_risk_level = str(risk_level)

    demo_alert = build_alert(
        location_name=location_name,
        region_name=region_name,
        risk_level=demo_risk_level,
        probability=demo_probability,
        river_name=river_name,
        river_level=river_level
    )

    if demo_risk_level == "CRITICAL":
        st.error("🚨 CRITICAL FLOOD-RISK CONDITION")
    elif demo_risk_level == "HIGH":
        st.warning("⚠️ HIGH FLOOD-RISK CONDITION")
    elif demo_risk_level == "MODERATE":
        st.warning("🟠 MODERATE FLOOD-RISK CONDITION")
    else:
        st.success("🟢 LOW FLOOD-RISK CONDITION")

    st.markdown(f"### Model Flood-Class Score: **{demo_probability:.1f}%**")
    st.write(f"**Alert:** {demo_alert['message']}")

    alert_a, alert_b, alert_c = st.columns(3)
    with alert_a:
        st.metric("Alert Level", demo_risk_level)
    with alert_b:
        st.metric("Model Score", f"{demo_probability:.1f}%")
    with alert_c:
        st.metric("Delivery", "READY")

    if st.button("📱 SEND DEMO SMS", type="primary", use_container_width=True):
        with st.spinner("Sending flood alert SMS..."):
            sms_ok, sms_message = send_flood_sms(
                location_name=location_name,
                region_name=region_name,
                risk_level=demo_risk_level,
                probability=demo_probability,
                river_name=river_name,
                river_level=river_level
            )

        if sms_ok:
            st.success("✅ SMS SENT TO VERIFIED MOBILE NUMBER")
            st.code(sms_message, language="text")
        else:
            st.error("❌ SMS NOT SENT")
            st.code(sms_message, language="text")

    st.info(
        "**Recommended action:** Move to safer/high ground and follow "
        "official emergency instructions."
    )

else:
    alert = build_alert(
        location_name=location_name,
        region_name=region_name,
        risk_level=risk_level,
        probability=probability,
        river_name=river_name,
        river_level=river_level
    )

    alert_level = alert["alert_level"]

    if alert_level == "CRITICAL":
        st.error(f"🚨 {alert['title']}")
    elif alert_level == "HIGH":
        st.warning(f"⚠️ {alert['title']}")
    elif alert_level == "MODERATE":
        st.warning(f"🟠 {alert['title']}")
    else:
        st.success(f"🟢 {alert['title']}")

    alert_a, alert_b, alert_c = st.columns(3)
    with alert_a:
        st.metric("Alert Level", alert_level)
    with alert_b:
        st.metric("Model Score", f"{probability:.2f}%")
    with alert_c:
        st.metric("Delivery", alert["delivery_status"])

    st.info(f"**Recommended action:** {alert['recommended_action']}")
    st.caption(f"Generated: {alert['timestamp']}")

st.caption(
    "Demo SMS uses Twilio Programmable Messaging. Production deployment "
    "requires an authorized alert policy and verified communication infrastructure."
)


# =========================================================
# PROJECT SCOPE
# =========================================================

st.divider()

st.subheader("🇮🇳 Project Scope")

st.write(
    "**FLOOD-AI is designed as a scalable India-wide "
    "decision-support platform, with a specialized "
    "flash-flood prediction workflow for hilly and "
    "high-risk regions.**"
)

st.write(
    "**Current detailed pilot:** Andhra Pradesh selected "
    "hilly and agency regions."
)

st.divider()

st.caption(
    "Prototype note: environmental values from the live "
    "weather/model service are current external data, while "
    "the current ML model is trained on synthetic/demo data. "
    "The current GSMaP satellite layer uses demonstration "
    "CSV data and is not a live satellite feed. River level "
    "is currently a demonstration input. Operational deployment "
    "requires historical observed flood labels, real-time "
    "hydrological integration, validated satellite/weather "
    "data fusion, model validation/calibration and authorized "
    "alert infrastructure. This system is not an operational "
    "emergency warning service."
)
