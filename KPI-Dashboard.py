import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


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


# Funktion zum Berechnen der KPIs
def calculate_kpis(df):
    # Beispielhafte Berechnungen:
    # Ladezeit: Differenz zwischen End- und Startzeit
    df['Ladezeit'] = (df['Endzeit'] - df['Startzeit']).dt.total_seconds() / 3600  # Ladezeit in Stunden

    # Ladeleistung (Annahme: Ladeleistung pro Stunde)
    df['Ladeleistung'] = df['Ladeenergie'] / df['Ladezeit']  # z.B. kWh / Stunden = kW

    # Gesamte Ladezeit
    total_ladezeit = df['Ladezeit'].sum()

    # Durchschnittliche Ladeleistung
    avg_ladeleistung = df['Ladeleistung'].mean()

    return total_ladezeit, avg_ladeleistung


# Streamlit-Oberfläche
# Setze die Seitenkonfiguration, um die volle Breite zu nutzen
st.set_page_config(page_title="Ladevorgangs-KPI-Analyse", layout="wide")

# Titel der App
st.title("Ladevorgangs-KPI-Analyse")

# Dateiupload-Funktion
uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch", type=["xlsx", "xls"])
if uploaded_file is not None:
    df = load_excel_file(uploaded_file)

    if df is not None:
        # Zeitspalten konvertieren
        df = convert_to_datetime(df, 'Startzeit', 'Endzeit')

        # KPIs berechnen
        total_ladezeit, avg_ladeleistung = calculate_kpis(df)

        # Anzeige der KPIs
        st.subheader("Berechnete KPIs über alle Ladevorgänge")
        st.write(f"Gesamte Ladezeit: {total_ladezeit:.2f} Stunden")
        st.write(f"Durchschnittliche Ladeleistung: {avg_ladeleistung:.2f} kW")

        # Daten filtern: Auswahl der Fahrzeuge oder Ladepunkte
        vehicle_filter = st.selectbox("Wählen Sie ein Fahrzeug:", df['Fahrzeug'].unique())
        filtered_df = df[df['Fahrzeug'] == vehicle_filter]

        # Visualisierung: Ladeleistung im Zeitverlauf
        st.subheader(f"Ladeleistung für {vehicle_filter}")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=filtered_df, x='Startzeit', y='Ladeleistung', ax=ax)
        ax.set_title('Ladeleistung im Zeitverlauf')
        ax.set_xlabel('Startzeit')
        ax.set_ylabel('Ladeleistung (kW)')
        st.pyplot(fig)

        # Datenübersicht in Tabelle
        st.subheader("Datenübersicht")
        st.write(filtered_df)
