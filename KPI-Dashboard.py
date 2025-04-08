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

# Funktion zum Konvertieren der Zeitspalten in datetime und Ladezeit berechnen
def convert_and_calculate_ladezeit(df, start_col, end_col):
    df[start_col] = pd.to_datetime(df[start_col], format='%d.%m.%Y %H:%M', errors='coerce')
    df[end_col] = pd.to_datetime(df[end_col], format='%d.%m.%Y %H:%M', errors='coerce')
    # Ladezeit berechnen (Differenz in Stunden)
    df['Ladezeit'] = (df[end_col] - df[start_col]).dt.total_seconds() / 3600
    return df

# Streamlit-Oberfläche
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")

# Titel der App
st.title("Historische Ladevorgänge (Verbrauch und Ladezeit)")

# Dateiupload
uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Datei laden
    df = load_excel_file(uploaded_file)

    if df is not None:
        # Konvertiere 'Startzeit' und 'Endzeit' zu datetime und berechne Ladezeit
        df = convert_and_calculate_ladezeit(df, 'Startzeit', 'Endzeit')

        # Darstellung des Verbrauchs als Liniendiagramm (Ladeenergie über Startzeit)
        st.subheader("Verbrauch der Ladevorgänge im Zeitverlauf")
        st.line_chart(df.set_index('Startzeit')['Ladeenergie'])
