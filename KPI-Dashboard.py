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
        # Zeige die Daten in einer Tabelle
        st.subheader("Datenübersicht")
        st.write(df)

        # Darstellung der Ladeenergie als Liniendiagramm
        if 'Ladeenergie' in df.columns:
            st.subheader("Verbrauch der Ladevorgänge (Ladeenergie)")
            st.line_chart(df['Ladeenergie'])
