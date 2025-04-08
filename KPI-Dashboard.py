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
    df[start_col] = pd.to_datetime(df[start_col], format='%d.%m.%Y %H:%M')
    df[end_col] = pd.to_datetime(df[end_col], format='%d.%m.%Y %H:%M')
    return df


# Streamlit-Oberfläche
def main():
    # Setze die Seitenkonfiguration, um die volle Breite zu nutzen
    st.set_page_config(page_title="Excel-Datenanzeige", layout="wide")

    # Titel der App
    st.title("Excel-Datenanzeige")

    # Dateiupload-Funktion
    uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # Excel-Datei laden
        df = load_excel_file(uploaded_file)

        if df is not None:
            # Konvertiere "Gestartet" und "Beendet" Spalten in Datetime
            start_col = 'Gestartet'  # Spaltenname für Startzeit
            end_col = 'Beendet'  # Spaltenname für Endzeit
            df = convert_to_datetime(df, start_col, end_col)

            # Anzeige der ersten Zeilen der Daten
            st.write("Datenvorschau:", df.head())

            # Möglichkeit zur Filterung/Anzeige bestimmter Spalten
            st.write("Spaltenauswahl:")
            columns = st.multiselect("Wähle Spalten zur Anzeige", df.columns.tolist(), default=df.columns.tolist())
            st.write(df[columns])

            # Schieberegler für den Zeitraum
            min_time = df[start_col].min()
            max_time = df[end_col].max()

            # Zeitraum-Auswahl mit Schieberegler
            selected_time_range = st.slider(
                "Wähle Zeitraum",
                min_value=min_time,
                max_value=max_time,
                value=(min_time, max_time),
                format="DD.MM.YYYY HH:mm"
            )

            # Filtere Daten basierend auf dem gewählten Zeitraum
            filtered_df = df[
                (df[start_col] >= selected_time_range[0]) &
                (df[end_col] <= selected_time_range[1])
                ]

            # Anzeige der gefilterten Daten
            st.write("Gefilterte Daten:", filtered_df)

            # Option, die vollständige Tabelle anzuzeigen
            if st.checkbox("Vollständige Tabelle anzeigen"):
                st.write(df)


if __name__ == "__main__":
    main()
