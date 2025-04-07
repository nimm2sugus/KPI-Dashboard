import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config("Ladeanalyse Dashboard", layout="wide")

st.title("🔌 Ladeanalyse Dashboard")

# Datei-Upload
uploaded_file = st.file_uploader("📁 Bereinigte Excel-Datei hochladen", type=["xlsx"])

if uploaded_file:
    # Daten einlesen
    df = pd.read_excel(uploaded_file)

    # Spalten vereinheitlichen
    df.columns = df.columns.str.strip()

    # Sicherstellen, dass wichtige Spalten vorhanden sind
    expected_cols = ['Standortname', 'Verbrauch (kWh)', 'Kosten', 'Standzeit', 'Gestartet', 'Beendet']
    if not all(col in df.columns for col in expected_cols):
        st.error("❌ Datei enthält nicht alle erwarteten Spalten.")
        st.stop()

    # Verbrauch & Kosten in Float konvertieren
    df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce')
    df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')

    # Standortfilter
    standorte = df['Standortname'].dropna().unique()
    selected = st.multiselect("🏢 Lade-Standorte filtern", standorte, default=list(standorte))
    df_filtered = df[df['Standortname'].isin(selected)]

    # Standort-KPIs gruppiert
    grouped = df_filtered.groupby('Standortname').agg({
        'Verbrauch_kWh': 'sum',
        'Kosten_EUR': 'sum'
    }).reset_index()

    # KPIs anzeigen
    st.subheader("🔢 KPIs nach Standort")
    st.dataframe(grouped, use_container_width=True)

    # Diagramme: Verbrauch & Kosten
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚡ Verbrauch nach Standort (kWh)")
        fig1 = px.bar(grouped, x="Standortname", y="Verbrauch_kWh", title="Gesamtverbrauch", color="Standortname")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("💶 Ladekosten nach Standort (€)")
        fig2 = px.bar(grouped, x="Standortname", y="Kosten_EUR", title="Gesamtkosten", color="Standortname")
        st.plotly_chart(fig2, use_container_width=True)

    # Pie-Charts + Monatsauswertung: Auth. Typ, Provider und monatliche KPIs
    st.subheader("📊 Detaillierte Auswertung pro Standort")

    for standort in selected:
        st.markdown(f"### 📍 {standort}")
        df_standort = df_filtered[df_filtered['Standortname'] == standort]

        # Pie-Charts
        pie_col1, pie_col2 = st.columns(2)

        with pie_col1:
            auth_counts = df_standort['Auth. Typ'].value_counts().reset_index()
            auth_counts.columns = ['Auth. Typ', 'Anzahl']
            fig_auth = px.pie(auth_counts, names='Auth. Typ', values='Anzahl',
                              title="Auth. Typ Verteilung")
            st.plotly_chart(fig_auth, use_container_width=True)

        with pie_col2:
            provider_counts = df_standort['Provider'].value_counts().reset_index()
            provider_counts.columns = ['Provider', 'Anzahl']
            fig_provider = px.pie(provider_counts, names='Provider', values='Anzahl',
                                  title="Provider Verteilung")
            st.plotly_chart(fig_provider, use_container_width=True)

        # Monatliche Verbrauchs- und Kostenauswertung
        if 'Monat (MM/JJJJ)' in df_standort.columns:
            df_monat = df_standort.groupby('Monat (MM/JJJJ)').agg({
                'Verbrauch_kWh': 'sum',
                'Kosten_EUR': 'sum'
            }).reset_index().sort_values('Monat (MM/JJJJ)')

            line_col1, line_col2 = st.columns(2)

            with line_col1:
                fig_verbrauch = px.line(df_monat,
                                        x='Monat (MM/JJJJ)',
                                        y='Verbrauch_kWh',
                                        title='Monatlicher Verbrauch (kWh)',
                                        markers=True)
                st.plotly_chart(fig_verbrauch, use_container_width=True)

            with line_col2:
                fig_kosten = px.line(df_monat,
                                     x='Monat (MM/JJJJ)',
                                     y='Kosten_EUR',
                                     title='Monatliche Kosten (€)',
                                     markers=True)
                st.plotly_chart(fig_kosten, use_container_width=True)
        else:
            st.warning("⚠️ 'Monat (MM/JJJJ)'-Spalte nicht gefunden. Monatliche Auswertung wird übersprungen.")

    # Optional: Tabelle mit Einzelwerten
    with st.expander("📄 Einzelne Ladevorgänge anzeigen"):
        st.dataframe(df_filtered, use_container_width=True)
