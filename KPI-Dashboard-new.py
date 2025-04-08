import streamlit as st
import pandas as pd
import re

st.title("🔌 Analyse von Ladevorgängen (Elektroladesäulen)")

# Datei-Upload
uploaded_file = st.file_uploader("📁 Bereinigte Excel-Datei hochladen", type=["xlsx"])

# Hilfsfunktion zum Parsen von "Standzeit"
def parse_standzeit(standzeit):
    if isinstance(standzeit, str):
        hours = int(re.search(r"(\d+)\s*Stunde", standzeit).group(1)) if re.search(r"(\d+)\s*Stunde", standzeit) else 0
        minutes = int(re.search(r"(\d+)\s*Minuten", standzeit).group(1)) if re.search(r"(\d+)\s*Minuten", standzeit) else 0
        seconds = int(re.search(r"(\d+)\s*Sekunden", standzeit).group(1)) if re.search(r"(\d+)\s*Sekunden", standzeit) else 0
        total_minutes = hours * 60 + minutes + seconds / 60
        return round(total_minutes, 2) if total_minutes > 0 else None
    return None

# Caching-Funktion für Datenverarbeitung
@st.cache_data
def load_and_prepare_excel(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()  # Spaltennamen bereinigen

    expected_cols = ['Standortname', 'Verbrauch', 'Kosten', 'Standzeit']
    missing_cols = [col for col in expected_cols if col not in df.columns]

    if missing_cols:
        return None, missing_cols

    # Standzeit umrechnen
    df["Standzeit_min"] = df["Standzeit"].apply(parse_standzeit)

    # Verbrauch & Kosten in Float konvertieren
    df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch'], errors='coerce')
    df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')
    # Verbrauch pro Minute berechnen (KPI)
    df["Verbrauch pro Minute"] = df.apply(
        lambda row: row["Verbrauch"] / row["Standzeit_min"] if row["Standzeit_min"] and row[ "Standzeit_min"] > 0 else None,
        axis=1)

    return df, missing_cols

# Verarbeitung starten
if uploaded_file:
    df, missing_cols = load_and_prepare_excel(uploaded_file)

    if df is None:
        st.error(f"❌ Die Datei enthält nicht alle erwarteten Spalten: {', '.join(missing_cols)}.")
        st.stop()

    st.success("✅ Datei erfolgreich verarbeitet!")
    st.dataframe(df)
