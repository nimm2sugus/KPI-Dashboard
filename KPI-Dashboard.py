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

# Funktion zum Berechnen der Ladezeit (Differenz zwischen Endzeit und Startzeit)
def calculate_ladezeit(df, start_col, end_col):
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
        # Berechnung der Ladezeit (falls Startzeit und Endzeit vorhanden sind)
        if 'Startzeit' in df.columns and 'Endzeit' in df.columns:
            df['Ladezeit'] = (df['Endzeit'] - df['Startzeit']).dt.total_seconds() / 3600

        # Darstellung des Verbrauchs als Liniendiagramm (Ladeenergie über Startzeit)
        st.subheader("Verbrauch der Ladevorgänge im Zeitverlauf")
        st.line_chart(df.set_index('Startzeit')['Ladeenergie'])
