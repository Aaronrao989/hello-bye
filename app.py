import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- SAFE OPTIONAL IMPORTS ----------------
try:
    import folium
    from streamlit_folium import st_folium
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Aadhaar Service Stress Model",
    layout="centered"
)

st.title("Aadhaar Service Stress Dashboard")
st.subheader("UIDAI Data Hackathon 2026")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("outputs/tables/aadhaar_service_stress_model_output.csv")
    df = df[df["state"].str.contains(r"[A-Za-z]", regex=True)]
    return df

model_df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.header("Select Region")

state = st.sidebar.selectbox(
    "State",
    sorted(model_df["state"].unique())
)

district = st.sidebar.selectbox(
    "District",
    sorted(model_df[model_df["state"] == state]["district"].unique())
)

row = model_df[
    (model_df["state"] == state) &
    (model_df["district"] == district)
].iloc[0]

# ---------------- METRICS ----------------
col1, col2, col3 = st.columns(3)
col1.metric("Total Enrolments", f"{int(row['total_enrolments']):,}")
col2.metric("Biometric Updates", f"{int(row['total_biometric_updates']):,}")
col3.metric("Demographic Updates", f"{int(row['total_demographic_updates']):,}")

st.divider()

# ---------------- SERVICE STRESS ----------------
st.subheader("Service Stress Assessment")
st.metric("Service Stress Score", f"{row['service_stress_score']:.2f}")
st.write(f"**Category:** {row['stress_category']}")

# Chart
fig, ax = plt.subplots(figsize=(6, 1.6))
ax.barh(["Service Stress"], [row["service_stress_score"]], color="red")
ax.set_xlim(0, model_df["service_stress_score"].max())
ax.set_title("Aadhaar Service Stress Indicator")

img_buffer = BytesIO()
fig.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
img_buffer.seek(0)

st.pyplot(fig)

st.download_button(
    "🖼️ Download Chart (PNG)",
    data=img_buffer,
    file_name=f"service_stress_{state}_{district}.png",
    mime="image/png"
)

st.divider()

# ---------------- PDF REPORT (DISTRICT) ----------------
def generate_pdf(row):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Aadhaar Service Stress Report")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Generated on: {timestamp}")

    y = height - 120
    c.setFont("Helvetica", 12)

    fields = [
        ("State", row["state"]),
        ("District", row["district"]),
        ("Total Enrolments", f"{int(row['total_enrolments']):,}"),
        ("Biometric Updates", f"{int(row['total_biometric_updates']):,}"),
        ("Demographic Updates", f"{int(row['total_demographic_updates']):,}"),
        ("Service Stress Score", f"{row['service_stress_score']:.2f}"),
        ("Priority Category", row["stress_category"]),
    ]

    for label, value in fields:
        c.drawString(50, y, f"{label}: {value}")
        y -= 22

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

st.subheader("Download District Report")

pdf_file = generate_pdf(row)

st.download_button(
    "📄 Download District Report (PDF)",
    data=pdf_file,
    file_name=f"aadhaar_service_stress_{state}_{district}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    mime="application/pdf"
)

st.divider()

# ---------------- STATE MAP VIEW ----------------
st.subheader("State-wise Service Stress Overview")

state_summary = model_df.groupby("state", as_index=False)["service_stress_score"].mean()

if MAP_AVAILABLE:
    india_map = folium.Map(location=[22.5, 78.9], zoom_start=5)

    for _, r in state_summary.iterrows():
        folium.Marker(
            location=[22.5, 78.9],  # conceptual overview
            tooltip=r["state"],
            popup=f"{r['state']}<br>Avg Stress: {r['service_stress_score']:.2f}"
        ).add_to(india_map)

    st_folium(india_map, width=700, height=450)
else:
    st.info("Map view unavailable (folium not available in this environment).")

st.divider()

# ---------------- BULK PDF (STATE SUMMARY) ----------------
def generate_state_summary_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "State-wise Aadhaar Service Stress Summary")

    y = height - 90
    c.setFont("Helvetica", 10)

    for _, r in df.iterrows():
        c.drawString(
            50, y,
            f"{r['state']}: Avg Stress Score = {r['service_stress_score']:.2f}"
        )
        y -= 18
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

state_pdf = generate_state_summary_pdf(state_summary)

st.subheader("Bulk Reports")

st.download_button(
    "📦 Download State-wise Summary (PDF)",
    data=state_pdf,
    file_name=f"aadhaar_state_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    mime="application/pdf"
)

st.divider()

st.caption(
    "This is an explainable decision-support system built using "
    "anonymised Aadhaar enrolment and update data."
)
