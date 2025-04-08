import streamlit as st
import pandas as pd


# Funktion zum Laden der Excel-Datei
@st.cache_data
def load_excel_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return None


# Streamlit-Seitenlayout
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")
st.title("Ladevorgangs-Daten Darstellung")

# Datei-Upload
uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = load_excel_file(uploaded_file)

    if df is not None:
        st.subheader("Datenübersicht")
        st.write(df)

        # Prüfen, ob "Beendet" vorhanden ist
        if 'Beendet' in df.columns:
            try:
                df['Beendet'] = pd.to_datetime(df['Beendet'])

                # Neue Zeit-Spalten extrahieren
                df['Tag'] = df['Beendet'].dt.date
                df['Monat'] = df['Beendet'].dt.to_period('M').astype(str)
                df['Jahr'] = df['Beendet'].dt.year
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten von 'Beendet': {e}")
        else:
            st.warning("Spalte 'Beendet' nicht gefunden.")

        # Verbrauch anzeigen
        if 'Verbrauch (kWh)' in df.columns:
            st.subheader("Verbrauch der Ladevorgänge (kWh)")
            st.line_chart(df.set_index('Beendet')['Verbrauch (kWh)'])

        # Kosten anzeigen + Aggregationen
        if 'Kosten' in df.columns:
            st.subheader("Kosten pro Ladevorgang (Einzeldaten)")
            st.line_chart(df.set_index('Beendet')['Kosten'])

            st.subheader("Tägliche Gesamtkosten")
            daily_costs = df.groupby('Tag')['Kosten'].sum()
            st.bar_chart(daily_costs)

            st.subheader("Monatliche Gesamtkosten")
            monthly_costs = df.groupby('Monat')['Kosten'].sum()
            st.bar_chart(monthly_costs)

            st.subheader("Jährliche Gesamtkosten")
            yearly_costs = df.groupby('Jahr')['Kosten'].sum()
            st.bar_chart(yearly_costs)
        else:
            st.warning("Spalte 'Kosten' nicht gefunden.")
