import streamlit as st
import pandas as pd
import plotly.express as px

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
st.title("🔌 Ladeanalyse Dashboard")

# Datei-Upload
uploaded_file = st.file_uploader("📁 Bereinigte Excel-Datei hochladen", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = load_excel_file(uploaded_file)

    if df is not None:
        st.subheader("Originaldaten")

        # Zeitspalten umwandeln
        df['Gestartet'] = pd.to_datetime(df['Gestartet'], errors='coerce')
        df['Beendet'] = pd.to_datetime(df['Beendet'], errors='coerce')

        # Verbrauch & Kosten umwandeln
        df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce')
        df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')

        # Ladezeit berechnen (in Stunden)
        df['Ladezeit_h'] = (df['Beendet'] - df['Gestartet']).dt.total_seconds() / 3600.0

        # Zeitdimensionen extrahieren
        df['Jahr'] = df['Beendet'].dt.year
        df['Monat'] = df['Beendet'].dt.month
        df['Tag'] = df['Beendet'].dt.day
        df['Stunde'] = df['Beendet'].dt.hour

        st.write(df)

        # Verbrauchsanalyse
        if 'Verbrauch_kWh' in df.columns:
            st.subheader("Aggregierter Verbrauch pro Stunde")
            df_stunde = df.groupby(df['Beendet'].dt.floor('H'))['Verbrauch_kWh'].sum().reset_index()
            st.line_chart(df_stunde.set_index('Beendet'))

            st.subheader("Aggregierter Verbrauch pro Tag")
            df_tag = df.groupby(df['Beendet'].dt.date)['Verbrauch_kWh'].sum().reset_index()
            df_tag['Beendet'] = pd.to_datetime(df_tag['Beendet'])
            st.line_chart(df_tag.set_index('Beendet'))

            st.subheader("Aggregierter Verbrauch pro Monat")
            df_monat = df.groupby(df['Beendet'].dt.to_period('M'))['Verbrauch_kWh'].sum().reset_index()
            df_monat['Beendet'] = df_monat['Beendet'].dt.to_timestamp()
            st.line_chart(df_monat.set_index('Beendet'))

            st.subheader("Aggregierter Verbrauch pro Jahr")
            df_jahr = df.groupby(df['Beendet'].dt.year)['Verbrauch_kWh'].sum().reset_index()
            df_jahr.columns = ['Jahr', 'Verbrauch_kWh']
            st.bar_chart(df_jahr.set_index('Jahr'))
        else:
            st.warning("Spalte 'Verbrauch_kWh' nicht gefunden.")

        # Verbrauch im Zeitverlauf
        st.subheader("Darstellungen")
        fig_line = px.line(df, x="Beendet", y="Verbrauch_kWh", title="Verbrauch [kWh]", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

        # KPIs nach Standort
        grouped = df.groupby('Standortname', as_index=False).agg({
            'Verbrauch_kWh': 'sum',
            'Kosten_EUR': 'sum'
        })

        st.subheader("🔢 Allgemeine KPIs nach Standort")
        st.dataframe(grouped, use_container_width=True)

        # Balkendiagramme
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⚡ Verbrauch nach Standort (kWh)")
            fig1 = px.bar(grouped, x="Standortname", y="Verbrauch_kWh", title="Gesamtverbrauch", color="Standortname")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("💶 Ladekosten nach Standort (€)")
            fig2 = px.bar(grouped, x="Standortname", y="Kosten_EUR", title="Gesamtkosten", color="Standortname")
            st.plotly_chart(fig2, use_container_width=True)

        # Detaillierte Auswertung pro Standort
        st.subheader("📊 Detaillierte Auswertung pro Standort")

        for standort in df['Standortname'].dropna().unique():
            st.markdown(f"### 📍 {standort}")
            df_standort = df[df['Standortname'] == standort]

            pie_col1, pie_col2 = st.columns(2)

            with pie_col1:
                auth_counts = df_standort['Auth. Typ'].value_counts().reset_index()
                auth_counts.columns = ['Auth. Typ', 'Anzahl']
                fig_auth = px.pie(auth_counts, names='Auth. Typ', values='Anzahl', title="Auth. Typ Verteilung")
                st.plotly_chart(fig_auth, use_container_width=True)

            with pie_col2:
                provider_counts = df_standort['Provider'].value_counts().reset_index()
                provider_counts.columns = ['Provider', 'Anzahl']
                fig_provider = px.pie(provider_counts, names='Provider', values='Anzahl', title="Provider Verteilung")
                st.plotly_chart(fig_provider, use_container_width=True)
