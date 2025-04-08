import streamlit as st
import pandas as pd
import altair as alt


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
        st.subheader("Originaldaten")
        st.write(df)

        # Sicherstellen, dass 'Beendet' eine Datetime-Spalte ist
        if 'Beendet' in df.columns:
            try:
                df['Beendet'] = pd.to_datetime(df['Beendet'])
                df['Jahr'] = df['Beendet'].dt.year
                df['Monat'] = df['Beendet'].dt.month
                df['Tag'] = df['Beendet'].dt.day
                df['Stunde'] = df['Beendet'].dt.hour
            except Exception as e:
                st.error(f"Fehler bei der Zeitumwandlung: {e}")
        else:
            st.warning("Spalte 'Beendet' nicht gefunden.")

        if 'Verbrauch (kWh)' in df.columns:
            # Aggregation pro Stunde
            st.subheader("Aggregierter Verbrauch pro Stunde")
            df_stunde = df.groupby([df['Beendet'].dt.floor('H')])['Verbrauch (kWh)'].sum().reset_index()
            st.line_chart(df_stunde.set_index('Beendet'))

            # Aggregation pro Tag
            st.subheader("Aggregierter Verbrauch pro Tag")
            df_tag = df.groupby([df['Beendet'].dt.date])['Verbrauch (kWh)'].sum().reset_index()
            df_tag['Beendet'] = pd.to_datetime(df_tag['Beendet'])  # wieder in datetime umwandeln
            st.line_chart(df_tag.set_index('Beendet'))

            # Aggregation pro Monat
            st.subheader("Aggregierter Verbrauch pro Monat")
            df_monat = df.groupby([df['Beendet'].dt.to_period('M')])['Verbrauch (kWh)'].sum().reset_index()
            df_monat['Beendet'] = df_monat['Beendet'].dt.to_timestamp()
            st.line_chart(df_monat.set_index('Beendet'))

            # Aggregation pro Jahr
            st.subheader("Aggregierter Verbrauch pro Jahr")
            df_jahr = df.groupby([df['Beendet'].dt.year])['Verbrauch (kWh)'].sum().reset_index()
            df_jahr.rename(columns={'Beendet': 'Jahr'}, inplace=True)
            st.bar_chart(df_jahr.set_index('Jahr'))

        else:
            st.warning("Spalte 'Verbrauch (kWh)' nicht gefunden.")
