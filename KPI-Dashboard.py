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

        # Verarbeite die Zeitspalte "Beendet"
        if 'Beendet' in df.columns:
            try:
                df['Beendet'] = pd.to_datetime(df['Beendet'])
                df = df.sort_values('Beendet')  # chronologisch sortieren
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten der Zeitspalte 'Beendet': {e}")
        else:
            st.warning("Spalte 'Beendet' nicht gefunden – Zeitaggregation nicht möglich.")

        # Verbrauch anzeigen
        if 'Verbrauch (kWh)' in df.columns:
            st.subheader("Verbrauch der Ladevorgänge (Ladeenergie in kWh)")
            st.line_chart(df.set_index('Beendet')['Verbrauch (kWh)'])

        # Kosten anzeigen
        if 'Kosten' in df.columns:
            st.subheader("Kosten für den User aller Ladevorgänge (Euro €)")
            st.line_chart(df.set_index('Beendet')['Kosten'])

            # Tägliche Gesamtkosten mit groupby
            st.subheader("Tägliche Gesamtkosten")
            df['Beendet_Datum'] = df['Beendet'].dt.date  # nur das Datum extrahieren
            daily_costs = df.groupby('Beendet_Datum')['Kosten'].sum()
            st.bar_chart(daily_costs)

            # Monatliche Gesamtkosten mit groupby
            st.subheader("Monatliche Gesamtkosten")
            df['Beendet_Monat'] = df['Beendet'].dt.to_period('M').astype(str)
            monthly_costs = df.groupby('Beendet_Monat')['Kosten'].sum()
            st.bar_chart(monthly_costs)
        else:
            st.warning("Spalte 'Kosten' nicht gefunden.")
