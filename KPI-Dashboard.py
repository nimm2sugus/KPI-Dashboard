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

def get_top_n_with_rest(series, top_n=10):
    top_values = series.value_counts().nlargest(top_n).index
    return series.where(series.isin(top_values), other='Rest')

# Streamlit-Seitenlayout
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")
st.title("🔌 Ladeanalyse Dashboard")

# Datei-Upload
uploaded_file = st.file_uploader("📁 Bereinigte Excel-Datei hochladen", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = load_excel_file(uploaded_file)

    if df is not None:
        st.subheader("Originaldaten nach Datenformatanpassung")

        df = df.copy()
        df['Gestartet'] = pd.to_datetime(df['Gestartet'], errors='coerce')
        df['Beendet'] = pd.to_datetime(df['Beendet'], errors='coerce')
        df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce')
        df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')
        df['Ladezeit_h'] = (df['Beendet'] - df['Gestartet']).dt.total_seconds() / 3600.0
        df['P_Schnitt'] = (df['Verbrauch_kWh'] / df['Ladezeit_h'])

        df['Jahr'] = df['Beendet'].dt.year
        df['Monat_num'] = df['Beendet'].dt.month
        df['Tag'] = df['Beendet'].dt.day
        df['Stunde'] = df['Beendet'].dt.hour

        st.write(df)

        grouped = df.groupby('Standortname', as_index=False).agg({
            'Verbrauch_kWh': 'mean',
            'Kosten_EUR': 'mean',
            'Ladezeit_h': 'mean',
            'P_Schnitt': 'mean',
            'Preisstellung': 'size'
        })

        grouped.columns = ['Standortname', 'Durchschnittsverbrauch pro LV [kWh]', 'Durchschnittskosten [Euro]',
                           'Durchschnittsladezeit [h]', 'Durchschnittsleistung [kWh]', 'Anzahl Ladevorgänge']

        st.subheader("🔢 Allgemeine KPIs nach Standort")
        st.dataframe(grouped, use_container_width=True)

        colors_auth = px.colors.qualitative.Plotly
        colors_provider = px.colors.qualitative.D3

        st.subheader("🌍 Auswertung über das gesamte Portfolio")
        portfolio_col1, portfolio_col2 = st.columns(2)

        with portfolio_col1:
            auth_counts_all = df['Auth. Typ'].value_counts().reset_index()
            auth_counts_all.columns = ['Auth. Typ', 'Anzahl']

            unique_auth_types_all = sorted(auth_counts_all['Auth. Typ'].tolist())
            color_map_auth_all = {auth_type: colors_auth[i % len(colors_auth)] for i, auth_type in
                                  enumerate(unique_auth_types_all)}

            fig_auth_all = px.pie(
                auth_counts_all,
                names='Auth. Typ',
                values='Anzahl',
                title="🔄 Auth. Typ Verteilung (gesamt)",
                color='Auth. Typ',
                color_discrete_map=color_map_auth_all
            )
            st.plotly_chart(fig_auth_all, use_container_width=True)

            auth_trend_all = (
                df
                .groupby([df['Beendet'].dt.to_period('M'), 'Auth. Typ'])
                .size()
                .reset_index(name='Anzahl')
            )
            auth_trend_all['Beendet'] = auth_trend_all['Beendet'].dt.to_timestamp()
            auth_trend_all['Prozent'] = auth_trend_all.groupby('Beendet')['Anzahl'].transform(
                lambda x: x / x.sum() * 100)

            fig_auth_trend_all = px.bar(
                auth_trend_all,
                x="Beendet",
                y="Prozent",
                color="Auth. Typ",
                title="📊 Prozentualer Verlauf der Auth. Typen (gesamt)",
                color_discrete_map=color_map_auth_all
            )
            fig_auth_trend_all.update_layout(barmode='stack', yaxis_title='Anteil [%]')
            st.plotly_chart(fig_auth_trend_all, use_container_width=True)

        with portfolio_col2:
            df_copy_all = df.copy()
            df_copy_all['Provider_kategorisiert'] = get_top_n_with_rest(df_copy_all['Provider'], top_n=10)

            provider_counts_all = df_copy_all.groupby('Provider_kategorisiert').size().reset_index(name='Anzahl')
            provider_counts_all = provider_counts_all.rename(columns={'Provider_kategorisiert': 'Provider'})

            unique_providers_all = sorted(provider_counts_all['Provider'].tolist())
            color_map_provider_all = {provider: colors_provider[i % len(colors_provider)] for i, provider in
                                      enumerate(unique_providers_all)}

            fig_provider_all = px.pie(
                provider_counts_all,
                names='Provider',
                values='Anzahl',
                title="🏢 Top 10 Provider + Rest (gesamt)",
                color='Provider',
                color_discrete_map=color_map_provider_all
            )
            st.plotly_chart(fig_provider_all, use_container_width=True)

            df_copy_all['Monat'] = df_copy_all['Beendet'].dt.to_period('M').dt.to_timestamp()
            prov_trend_all = (
                df_copy_all
                .groupby(['Monat', 'Provider_kategorisiert'])
                .size()
                .reset_index(name='Anzahl')
            )
            prov_trend_all['Prozent'] = prov_trend_all.groupby('Monat')['Anzahl'].transform(lambda x: x / x.sum() * 100)

            fig_prov_trend_all = px.bar(
                prov_trend_all,
                x="Monat",
                y="Prozent",
                color="Provider_kategorisiert",
                title="📊 Prozentualer Verlauf der Provider (gesamt)",
                color_discrete_map=color_map_provider_all
            )
            fig_prov_trend_all.update_layout(barmode='stack', yaxis_title='Anteil [%]')
            st.plotly_chart(fig_prov_trend_all, use_container_width=True)

        st.subheader("📊 Detaillierte Auswertung pro Standort")

        for standort in df['Standortname'].dropna().unique():
            st.markdown(f"### 📍 {standort}")
            df_standort = df[df['Standortname'] == standort].copy()

            # ✅ Korrigierter Teil für Verbrauch pro Monat:
            verbrauch_monat = (
                df_standort
                .groupby(df_standort['Beendet'].dt.to_period('M'))['Verbrauch_kWh']
                .sum()
                .reset_index()
                .rename(columns={'Beendet': 'Monat', 'Verbrauch_kWh': 'Gesamtverbrauch_kWh'})
            )
            verbrauch_monat['Monat'] = verbrauch_monat['Monat'].dt.to_timestamp()

            fig_sum_monat = px.bar(
                verbrauch_monat,
                x='Monat',
                y='Gesamtverbrauch_kWh',
                title='📊 Verbrauch pro Monat',
                labels={'Gesamtverbrauch_kWh': 'Gesamtverbrauch (kWh)', 'Monat': 'Monat'},
                color='Gesamtverbrauch_kWh',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig_sum_monat, use_container_width=True)

            auth_col, prov_col = st.columns(2)

            with auth_col:
                auth_counts = df_standort['Auth. Typ'].value_counts().reset_index()
                auth_counts.columns = ['Auth. Typ', 'Anzahl']
                unique_auth_types = sorted(auth_counts['Auth. Typ'].tolist())
                color_map_auth = {auth_type: colors_auth[i % len(colors_auth)] for i, auth_type in
                                  enumerate(unique_auth_types)}

                fig_auth = px.pie(
                    auth_counts,
                    names='Auth. Typ',
                    values='Anzahl',
                    title="🔄 Auth. Typ Verteilung",
                    color='Auth. Typ',
                    color_discrete_map=color_map_auth
                )
                st.plotly_chart(fig_auth, use_container_width=True)

                auth_trend = (
                    df_standort
                    .groupby([df_standort['Beendet'].dt.to_period('M'), 'Auth. Typ'])
                    .size()
                    .reset_index(name='Anzahl')
                )
                auth_trend['Beendet'] = auth_trend['Beendet'].dt.to_timestamp()
                auth_trend['Prozent'] = auth_trend.groupby('Beendet')['Anzahl'].transform(lambda x: x / x.sum() * 100)

                fig_auth_trend = px.bar(
                    auth_trend,
                    x="Beendet",
                    y="Prozent",
                    color="Auth. Typ",
                    title="📊 Verlauf Auth. Typ [%]",
                    color_discrete_map=color_map_auth
                )
                fig_auth_trend.update_layout(barmode='stack', yaxis_title='Anteil [%]')
                st.plotly_chart(fig_auth_trend, use_container_width=True)

            with prov_col:
                df_standort_copy = df_standort.copy()
                df_standort_copy['Provider_kategorisiert'] = get_top_n_with_rest(df_standort_copy['Provider'], top_n=10)
                provider_counts = df_standort_copy.groupby('Provider_kategorisiert').size().reset_index(name='Anzahl')
                provider_counts = provider_counts.rename(columns={'Provider_kategorisiert': 'Provider'})

                unique_providers = sorted(provider_counts['Provider'].tolist())
                color_map_provider = {provider: colors_provider[i % len(colors_provider)] for i, provider in
                                      enumerate(unique_providers)}

                fig_provider = px.pie(
                    provider_counts,
                    names='Provider',
                    values='Anzahl',
                    title="🏢 Top 10 Provider + Rest",
                    color='Provider',
                    color_discrete_map=color_map_provider
                )
                st.plotly_chart(fig_provider, use_container_width=True)

                df_standort_copy['Monat'] = df_standort_copy['Beendet'].dt.to_period('M').dt.to_timestamp()
                prov_trend = (
                    df_standort_copy
                    .groupby(['Monat', 'Provider_kategorisiert'])
                    .size()
                    .reset_index(name='Anzahl')
                )
                prov_trend['Prozent'] = prov_trend.groupby('Monat')['Anzahl'].transform(lambda x: x / x.sum() * 100)

                fig_prov_trend = px.bar(
                    prov_trend,
                    x="Monat",
                    y="Prozent",
                    color="Provider_kategorisiert",
                    title="📊 Verlauf Provider [%]",
                    color_discrete_map=color_map_provider
                )
                fig_prov_trend.update_layout(barmode='stack', yaxis_title='Anteil [%]')
                st.plotly_chart(fig_prov_trend, use_container_width=True)
