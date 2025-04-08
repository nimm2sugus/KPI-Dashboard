import streamlit as st
import pandas as pd
import numpy as np

# Funktion zum Laden der Excel-Datei
@st.cache_data
def load_excel_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return None

# Streamlit-Oberfläche
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")

# Titel der App
st.title("Ladevorgangs-Daten Darstellung")

# Dateiupload
uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Datei laden
    df = load_excel_file(uploaded_file)

    if df is not None:
        st.subheader("Datenübersicht")
        st.write(df)

        # Zeitspalte "Beendet" als Zeitindex verwenden
        if 'Beendet' in df.columns:
            try:
                df['Beendet'] = pd.to_datetime(df['Beendet'])
                df = df.sort_values('Beendet')  # chronologisch ordnen
                df.set_index('Beendet', inplace=True)
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten der Beendet-Spalte: {e}")
        else:
            st.warning("Spalte 'Beendet' nicht gefunden – Zeitreihen nicht möglich.")

        # Liniendiagramm: Verbrauch
        if 'Verbrauch (kWh)' in df.columns:
            st.subheader("Verbrauch der Ladevorgänge (Ladeenergie in kWh)")
            st.line_chart(df['Verbrauch (kWh)'])

        # Liniendiagramm: Kosten
        if 'Kosten' in df.columns:
            st.subheader("Kosten für den User aller Ladevorgänge (Euro €)")
            st.line_chart(df['Kosten'])

            # Aggregation pro Tag
            st.subheader("Tägliche Gesamtkosten")
            try:
                daily_costs = df['Kosten'].resample('D').sum()
                st.bar_chart(daily_costs)
            except Exception as e:
                st.warning(f"Fehler bei Tagesaggregation: {e}")

            # Aggregation pro Monat
            st.subheader("Monatliche Gesamtkosten")
            try:
                monthly_costs = df['Kosten'].resample('M').sum()
                st.bar_chart(monthly_costs)
            except Exception as e:
                st.warning(f"Fehler bei Monatsaggregation: {e}")

        else:
            st.warning("Spalte 'Kosten' nicht gefunden.")
