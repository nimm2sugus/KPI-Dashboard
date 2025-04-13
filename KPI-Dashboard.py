import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_excel_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return None

# Funktion: Top-N + Rest gruppieren
def get_top_n_with_rest(series, top_n=10):
    top_values = series.value_counts().nlargest(top_n).index
    return series.where(series.isin(top_values), other='Rest')

# Streamlit Layout
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")
st.title("🔌 Ladeanalyse Dashboard")

uploaded_file = st.file_uploader("📁 Bereinigte Excel-Datei hochladen", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = load_excel_file(uploaded_file)

    if df is not None:
        st.subheader("Originaldaten")

        df['Gestartet'] = pd.to_datetime(df['Gestartet'], errors='coerce')
        df['Beendet'] = pd.to_datetime(df['Beendet'], errors='coerce')

        # neue Datenspalten
        df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce')
        df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')
        df['Ladezeit_h'] = (df['Beendet'] - df['Gestartet']).dt.total_seconds() / 3600.0
        df['Anzahl_Ladevorgänge'] = df.count(df['Verbrauch (kWh)'])
        df['P_Schnitt'] = df['Verbrauch_kWh'] / df['Ladezeit_h']

        # unnötiges Time-Handling???
        df['Jahr'] = df['Beendet'].dt.year
        df['Monat'] = df['Beendet'].dt.month
        df['Tag'] = df['Beendet'].dt.day
        df['Stunde'] = df['Beendet'].dt.hour

        # streamlit Tabellendarstellung - Handling ausbaufähig
        st.write(df)

        monatsnamen = {
            1: "Januar", 2: "Februar", 3: "März", 4: "April",
            5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
            9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
        }
        df['Monat_name'] = df['Monat'].map(monatsnamen)
        df['Monat_name'] = pd.Categorical(df['Monat_name'], categories=list(monatsnamen.values()), ordered=True)

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
            st.bar_chart(df_monat.set_index('Beendet'))

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

        # Durchschnittlicher Verbrauch pro Monat
        avg_verbrauch_monat = df.groupby('Monat_name')['Verbrauch_kWh'].mean().reset_index()
        fig_avg_monat = px.bar(
            avg_verbrauch_monat,
            x='Monat_name',
            y='Verbrauch_kWh',
            title='📊 Durchschnittlicher Verbrauch pro Monat',
            labels={'Verbrauch_kWh': 'Ø Verbrauch (kWh)', 'Monat_name': 'Monat'},
            color='Verbrauch_kWh',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_avg_monat, use_container_width=True)

        # Gruppierung für Tabellendarstellung nach Gesamtdurchschnitt - Auswahl Datendarstellung ausstehend
        grouped = df.groupby('Standortname', as_index=False).agg(
            Verbrauch_kWh_sum=('Verbrauch_kWh', 'sum'),
            Verbrauch_kWh_mean=('Verbrauch_kWh', 'mean'),
            Kosten_EUR_sum=('Kosten_EUR', 'sum'),
            Kosten_EUR_mean=('Kosten_EUR', 'mean'),
            P_Schnitt_mean=('P_Schnitt', 'mean'),
            Ladezeit_h = ('Kosten_EUR', 'mean'),
            Anzahl_Ladevorgaenge=('Verbrauch_kWh', 'count')
        )
        # streamlit Tabellendarstellen
        st.subheader("🔢 Allgemeine KPIs nach Standort")
        st.dataframe(grouped, use_container_width=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("⚡ Verbrauch nach Standort (kWh)")
            fig1 = px.bar(grouped, x="Standortname", y="Verbrauch_kWh_sum", title="Gesamtverbrauch", color="Standortname")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("💶 Ladekosten für den User nach Standort (€)")
            fig2 = px.bar(grouped, x="Standortname", y="Kosten_EUR_sum", title="Gesamtkosten", color="Standortname")
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            st.subheader("Durchschnittlicher Leistung pro Ladevorgang")
            fig3 = px.bar(grouped, x="Standortname", y="Kosten_EUR_mean", title="Durchschnittliche Leistung", color="Standortname")
            st.plotly_chart(fig3, use_container_width=True)

        st.subheader("📊 Detaillierte Auswertung pro Standort")

        for standort in df['Standortname'].dropna().unique():
            st.markdown(f"### 📍 {standort}")
            df_standort = df[df['Standortname'] == standort]

            # Tagesdurchschnitt
            avg_verbrauch_tag = df_standort.groupby('Tag')['Verbrauch_kWh_sum'].mean().reset_index()
            fig_avg_tag = px.bar(
                avg_verbrauch_tag,
                x='Tag',
                y='Verbrauch_kWh_sum',
                title='📊 Durchschnittlicher Verbrauch pro Tag',
                labels={'Verbrauch_kWh_sum': 'Ø Verbrauch (kWh)', 'Tag': 'Tag'},
                color='Verbrauch_kWh_sum',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_avg_tag, use_container_width=True)

            pie_col1, line_col1 = st.columns(2)

            with pie_col1:
                df_standort['Auth_Typ_kategorisiert'] = get_top_n_with_rest(df_standort['Auth. Typ'], top_n=10)
                auth_counts = df_standort['Auth_Typ_kategorisiert'].value_counts().reset_index()
                auth_counts.columns = ['Auth. Typ', 'Anzahl']
                fig_auth = px.pie(auth_counts, names='Auth. Typ', values='Anzahl', title="Top 10 Auth. Typen + Rest")
                st.plotly_chart(fig_auth, use_container_width=True)

            with line_col1:
                df_standort['Auth_Typ_kategorisiert'] = get_top_n_with_rest(df_standort['Auth. Typ'], top_n=10)
                auth_trend = df_standort.groupby(['Monat_name', 'Auth_Typ_kategorisiert']).size().reset_index(name='Anzahl')
                fig_auth_trend = px.line(
                    auth_trend,
                    x="Monat_name",
                    y='Anzahl',
                    color='Auth_Typ_kategorisiert',
                    markers=True,
                    title="Verlauf der Auth. Typen (Top 10 + Rest)"
                )
                st.plotly_chart(fig_auth_trend, use_container_width=True)

            pie_col2, line_col2 = st.columns(2)

            with pie_col2:
                df_standort['Provider_kategorisiert'] = get_top_n_with_rest(df_standort['Provider'], top_n=10)
                provider_counts = df_standort['Provider_kategorisiert'].value_counts().reset_index()
                provider_counts.columns = ['Provider', 'Anzahl']
                fig_provider = px.pie(provider_counts, names='Provider', values='Anzahl', title="Top 10 Provider + Rest")
                st.plotly_chart(fig_provider, use_container_width=True)

            with line_col2:
                df_standort['Provider_kategorisiert'] = get_top_n_with_rest(df_standort['Provider'], top_n=10)
                prov_trend = df_standort.groupby(['Monat_name', 'Provider_kategorisiert']).size().reset_index(name='Anzahl')
                fig_prov_trend = px.line(
                    prov_trend,
                    x="Monat_name",
                    y='Anzahl',
                    color='Provider_kategorisiert',
                    markers=True,
                    title="Verlauf der Provider (Top 10 + Rest)"
                )
                st.plotly_chart(fig_prov_trend, use_container_width=True)
