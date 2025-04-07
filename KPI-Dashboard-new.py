import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config("Ladeanalyse Dashboard", layout="wide")

st.title("🔌 Ladeanalyse Dashboard")

# Datei-Upload
uploaded_file = st.file_uploader("📁 Bereinigte Excel-Datei hochladen", type=["xlsx"])

if uploaded_file:
    # Daten einlesen
    df = pd.read_excel(uploaded_file)

    # Spalten vereinheitlichen
    df.columns = df.columns.str.strip()

    # Sicherstellen, dass wichtige Spalten vorhanden sind
    expected_cols = ['Standortname', 'Verbrauch (kWh)', 'Kosten', 'Standzeit', 'Gestartet', 'Beendet']
    if not all(col in df.columns for col in expected_cols):
        st.error("❌ Datei enthält nicht alle erwarteten Spalten.")
        st.stop()

    # Verbrauch & Kosten in Float konvertieren
    df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce')
    df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')

    # Standortfilter
    standorte = df['Standortname'].dropna().unique()
    selected = st.multiselect("🏢 Lade-Standorte filtern", standorte, default=list(standorte))
    df_filtered = df[df['Standortname'].isin(selected)]

    # Standort-KPIs gruppiert
    grouped = df_filtered.groupby('Standortname').agg({
        'Verbrauch_kWh': 'sum',
        'Kosten_EUR': 'sum'
    }).reset_index()

    # KPIs anzeigen
    st.subheader("🔢 KPIs nach Standort")
    st.dataframe(grouped, use_container_width=True)

    # Diagramme
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚡ Verbrauch nach Standort (kWh)")
        fig1 = px.bar(grouped, x="Standortname", y="Verbrauch_kWh", title="Gesamtverbrauch", color="Standortname")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("💶 Kosten nach Standort (€)")
        fig2 = px.bar(grouped, x="Standortname", y="Kosten_EUR", title="Gesamtkosten", color="Standortname")
        st.plotly_chart(fig2, use_container_width=True)

    # Optional: Tabelle mit Einzelwerten
    with st.expander("📄 Einzelne Ladevorgänge anzeigen"):
        st.dataframe(df_filtered, use_container_width=True)