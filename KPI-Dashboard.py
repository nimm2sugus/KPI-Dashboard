import streamlit as st
import pandas as pd


# Funktion zum Laden der Excel-Datei
@st.cache_data
def load_excel_file(uploaded_file):
    try:
        # Versuchen, die Excel-Datei zu laden
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return None


# Funktion zum Konvertieren der Zeitspalten in datetime
def convert_to_datetime(df, start_col, end_col):
    try:
        df[start_col] = pd.to_datetime(df[start_col], format='%d.%m.%Y %H:%M', errors='coerce')
        df[end_col] = pd.to_datetime(df[end_col], format='%d.%m.%Y %H:%M', errors='coerce')
    except KeyError as e:
        st.error(f"Spalte '{e}' nicht gefunden!")
    except Exception as e:
        st.error(f"Fehler bei der Konvertierung der Zeitspalten: {e}")
    return df


# Streamlit-Oberfläche
# Setze die Seitenkonfiguration, um die volle Breite zu nutzen
st.set_page_config(page_title="Excel-Datenanzeige", layout="wide")

# Titel der App
st.title("Excel-Datenanzeige")

# Dateiupload-Funktion
uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Excel-Datei laden
    with st.spinner('Lade die Datei...'):
        df = load_excel_file(uploaded_file)

    if df is not None:
        # Zeige die ersten Zeilen der geladenen Daten
        st.write("Erste Zeilen der Datei:")
        st.write(df.head())

        # Konvertiere "Gestartet" und "Beendet" Spalten in Datetime, falls sie vorhanden sind
        start_col = 'Gestartet'  # Spaltenname für Startzeit
        end_col = 'Beendet'  # Spaltenname für Endzeit

        if start_col in df.columns and end_col in df.columns:
            df = convert_to_datetime(df, start_col, end_col)
        else:
            st.warning(f"Die Spalten '{start_col}' oder '{end_col}' wurden nicht gefunden!")

        # Möglichkeit zur Filterung/Anzeige bestimmter Spalten
        st.write("Spaltenauswahl:")
        columns = st.multiselect("Wähle Spalten zur Anzeige", df.columns.tolist(), default=df.columns.tolist())

        # Zeige den gefilterten DataFrame
        if columns:
            st.write(df[columns])
