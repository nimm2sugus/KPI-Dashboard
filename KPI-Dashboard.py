import streamlit as st
import pandas as pd

# Funktion zum Laden der Excel-Datei
def load_excel_file(uploaded_file):
    try:
        # Versuchen, die Excel-Datei zu laden
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return None

# Streamlit-Oberfläche
def main():
    # Titel der App
    st.title("Excel-Datenanzeige")

    # Dateiupload-Funktion
    uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # Excel-Datei laden
        df = load_excel_file(uploaded_file)

        if df is not None:
            # Anzeige der ersten Zeilen der Daten
            st.write("Datenvorschau:", df.head())

            # Möglichkeit zur Filterung/Anzeige bestimmter Spalten
            st.write("Spaltenauswahl:")
            columns = st.multiselect("Wähle Spalten zur Anzeige", df.columns.tolist(), default=df.columns.tolist())
            st.write(df[columns])

            # Option, die vollständige Tabelle anzuzeigen
            if st.checkbox("Vollständige Tabelle anzeigen"):
                st.write(df)

if __name__ == "__main__":
    main()
