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

        # Kopie für Bearbeitung
        df = df.copy()

        # Zeitspalten umwandeln
        df['Gestartet'] = pd.to_datetime(df['Gestartet'], errors='coerce')
        df['Beendet'] = pd.to_datetime(df['Beendet'], errors='coerce')

        # Verbrauch & Kosten umwandeln
        df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce')
        df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')

        # Ladezeit berechnen (in Stunden)
        df['Ladezeit_h'] = (df['Beendet'] - df['Gestartet']).dt.total_seconds() / 3600.0

        # Durchschnittsleistung berechnen
        df['P_Schnitt'] = (df['Verbrauch_kWh'] / df['Ladezeit_h'])

        # Zeitdimensionen extrahieren
        df['Jahr'] = df['Beendet'].dt.year
        df['Monat_num'] = df['Beendet'].dt.month
        df['Tag'] = df['Beendet'].dt.day
        df['Stunde'] = df['Beendet'].dt.hour

        st.write(df)


        # KPIs nach Standort
        grouped = df.groupby('Standortname', as_index=False).agg({
            'Verbrauch_kWh': 'mean',
            'Kosten_EUR': 'mean',
            'Ladezeit_h': 'mean',
            'P_Schnitt': 'mean',
            'Preisstellung': 'size'
        })

        # Header umbenennen
        grouped.columns = ['Standortname', 'Durchschnittsverbrauch pro LV [kWh]', 'Durchschnittskosten [Euro]',
                           'Durchschnittsladezeit [h]', 'Durchschnittsleistung [kWh]', 'Anzahl Ladevorgänge']

        st.subheader("🔢 Allgemeine KPIs nach Standort")
        st.dataframe(grouped, use_container_width=True)


        # Farbpalette für Auth Typ
        colors_auth = px.colors.qualitative.Plotly  # Palette 1
        # Farbpalette für Provider (eine andere als oben!)
        colors_provider = px.colors.qualitative.D3  # Palette 2


        # 🔍 Gesamtauswertung für das gesamte Portfolio
        st.subheader("🌍 Auswertung über das gesamte Portfolio")

        portfolio_col1, portfolio_col2 = st.columns(2)

        # ---------------- AUTH TYP (Gesamt) ----------------
        with portfolio_col1:
            auth_counts_all = df['Auth. Typ'].value_counts().reset_index()
            auth_counts_all.columns = ['Auth. Typ', 'Anzahl']

            unique_auth_types_all = sorted(auth_counts_all['Auth. Typ'].tolist())
            color_map_auth_all = {auth_type: colors_auth[i % len(colors_auth)] for i, auth_type in
                                  enumerate(unique_auth_types_all)}

            # Pie Chart für alle Standorte
            fig_auth_all = px.pie(
                auth_counts_all,
                names='Auth. Typ',
                values='Anzahl',
                title="🔄 Auth. Typ Verteilung (gesamt)",
                color='Auth. Typ',
                color_discrete_map=color_map_auth_all
            )
            st.plotly_chart(fig_auth_all, use_container_width=True)

            # Zeitverlauf (Prozent)
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

        # ---------------- PROVIDER (Gesamt) ----------------
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

            # Zeitverlauf (Prozent)
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


        # Detaillierte Auswertung pro Standort
        st.subheader("📊 Detaillierte Auswertung pro Standort")

        for standort in df['Standortname'].dropna().unique():
            st.markdown(f"### 📍 {standort}")

            df_standort = df[df['Standortname'] == standort].copy()

            # Durchschnittlicher Verbrauch pro Tag (pro Standort)
            avg_verbrauch_tag = df_standort.groupby('Tag')['Verbrauch_kWh'].mean().reset_index(name='Verbrauch_kWh_mean')
            fig_avg_tag = px.bar(
                avg_verbrauch_tag,
                x='Tag',
                y='Verbrauch_kWh_mean',
                title='📊 Durchschnittlicher Verbrauch pro Tag',
                labels={'Verbrauch_kWh_mean': 'Ø Verbrauch (kWh)', 'Tag': 'Tag'},
                color='Verbrauch_kWh_mean',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_avg_tag, use_container_width=True)

            pie_col1, line_col1 = st.columns(2)

            # --- Pie Chart Auth Typ ---
            with pie_col1:
                auth_counts = df_standort['Auth. Typ'].value_counts().reset_index()
                auth_counts.columns = ['Auth. Typ', 'Anzahl']

                # Sortiere die Auth-Typen alphabetisch
                unique_auth_types = sorted(auth_counts['Auth. Typ'].tolist())
                color_map_auth = {auth_type: colors_auth[i % len(colors_auth)] for i, auth_type in
                                  enumerate(unique_auth_types)}

                fig_auth = px.pie(
                    auth_counts,
                    names='Auth. Typ',
                    values='Anzahl',
                    title="Auth. Typ Verteilung",
                    color='Auth. Typ',  # Dies stellt sicher, dass die Farben korrekt zugewiesen werden
                    color_discrete_map=color_map_auth  # Farbzuordnung für das Pie-Chart
                )
                st.plotly_chart(fig_auth, use_container_width=True)

            with line_col1:
                auth_trend = (
                    df_standort
                    .groupby([df_standort['Beendet'].dt.to_period('M'), 'Auth. Typ'])
                    .size()
                    .reset_index(name='Anzahl')
                )
                auth_trend['Beendet'] = auth_trend['Beendet'].dt.to_timestamp()

                # Berechne prozentuale Anteile je Monat
                auth_trend['Prozent'] = auth_trend.groupby('Beendet')['Anzahl'].transform(lambda x: x / x.sum() * 100)

                fig_auth_trend = px.bar(
                    auth_trend,
                    x="Beendet",
                    y="Prozent",
                    color="Auth. Typ",
                    title="📊 Prozentualer Verlauf der Auth. Typen im Zeitverlauf",
                    color_discrete_map=color_map_auth
                )

                fig_auth_trend.update_layout(barmode='stack', yaxis_title='Anteil [%]')

                st.plotly_chart(fig_auth_trend, use_container_width=True)

            # -------------------------------------------------------------------

            pie_col2, line_col2 = st.columns(2)

            # --- Pie Chart Provider ---
            with pie_col2:
                df_standort_copy = df_standort.copy()
                df_standort_copy['Provider_kategorisiert'] = get_top_n_with_rest(df_standort_copy['Provider'], top_n=10)

                provider_counts = df_standort_copy.groupby('Provider_kategorisiert').size().reset_index(name='Anzahl')
                provider_counts = provider_counts.rename(columns={'Provider_kategorisiert': 'Provider'})

                # Sortiere die Provider alphabetisch
                unique_providers = sorted(provider_counts['Provider'].tolist())
                color_map_provider = {provider: colors_provider[i % len(colors_provider)] for i, provider in
                                      enumerate(unique_providers)}

                fig_provider = px.pie(
                    provider_counts,
                    names='Provider',
                    values='Anzahl',
                    title="Top 10 Provider + Rest",
                    color='Provider',  # Dies stellt sicher, dass die Farben korrekt zugewiesen werden
                    color_discrete_map=color_map_provider  # Farbzuordnung für das Pie-Chart
                )
                st.plotly_chart(fig_provider, use_container_width=True)

            with line_col2:
                df_standort_copy['Monat'] = df_standort_copy['Beendet'].dt.to_period('M').dt.to_timestamp()

                prov_trend = (
                    df_standort_copy
                    .groupby(['Monat', 'Provider_kategorisiert'])
                    .size()
                    .reset_index(name='Anzahl')
                )

                # Berechne prozentuale Anteile je Monat
                prov_trend['Prozent'] = prov_trend.groupby('Monat')['Anzahl'].transform(lambda x: x / x.sum() * 100)

                fig_prov_trend = px.bar(
                    prov_trend,
                    x="Monat",
                    y="Prozent",
                    color="Provider_kategorisiert",
                    title="📊 Prozentualer Verlauf der Provider (Top 10 + Rest)",
                    color_discrete_map=color_map_provider
                )

                fig_prov_trend.update_layout(barmode='stack', yaxis_title='Anteil [%]')

                st.plotly_chart(fig_prov_trend, use_container_width=True)
