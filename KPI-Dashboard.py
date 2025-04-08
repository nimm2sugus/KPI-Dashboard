import streamlit as st
import pandas as pd

# Lade Excel-Datei
def load_data():
    # Lade die Excel-Datei und gebe den DataFrame zurück
    return pd.read_excel('data.xlsx', engine='openpyxl')

# Berechnung von KPIs
def calculate_kpis(df):
    kpis = {
        "Durchschnitt Ladeleistung (kW)": df['Ladeleistung'].mean(),
        "Durchschnitt Ladedauer (Minuten)": df['Ladedauer'].mean(),
        "Durchschnitt Energie (kWh)": df['Energie'].mean(),
    }
    return kpis

# Streamlit App
def app():
    st.title('Ladevorgangs-Datenanalyse')

    # Lade die Daten
    df = load_data()

    # Zeige die ersten 5 Zeilen der Daten an
    st.subheader('Datenvorschau')
    st.dataframe(df.head())

    # Berechne KPIs und zeige sie an
    kpis = calculate_kpis(df)
    st.subheader('KPIs')
    for key, value in kpis.items():
        st.write(f"{key}: {value:.2f}")

    # Visualisierung: Durchschnittliche Ladeleistung pro Tag
    st.subheader('Durchschnittliche Ladeleistung pro Tag')
    daily_performance = df.groupby('Datum')['Ladeleistung'].mean().reset_index()
    st.line_chart(daily_performance.set_index('Datum'))

    # Visualisierung: Gesamtenergieverbrauch pro Ladepunkt
    st.subheader('Gesamtenergieverbrauch pro Ladepunkt')
    energy_per_point = df.groupby('Ladepunkt')['Energie'].sum().reset_index()
    st.bar_chart(energy_per_point.set_index('Ladepunkt'))

if __name__ == "__main__":
    app()
