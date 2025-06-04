import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request

# Streamlit-Seitenlayout
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")

# Funktion zum Laden der Excel-Datei (Upload oder URL)
@st.cache_data
def load_excel_file(source, from_url=False):
    try:
        if from_url:
            response = urllib.request.urlopen(source)
            df = pd.read_excel(response, engine='openpyxl')
        else:
            df = pd.read_excel(source, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return None

def get_top_n_with_rest(series, top_n=10):
    top_values = series.value_counts().nlargest(top_n).index
    return series.where(series.isin(top_values), other='Rest')

st.title("🔌 Ladeanalyse Dashboard")

# Auswahlmöglichkeit: Upload oder SharePoint-Link
input_method = st.radio("📂 Datenquelle wählen:", ["Datei-Upload", "SharePoint-Link"])

df = None

if input_method == "Datei-Upload":
    uploaded_file = st.file_uploader("📁 Bereinigte Excel-Datei hochladen", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = load_excel_file(uploaded_file)
        if df is not None:
            st.success("Datei erfolgreich geladen.")

elif input_method == "SharePoint-Link":
    sharepoint_url = st.text_input("🔗 Öffentlicher SharePoint-Download-Link zur Excel-Datei", "")
    if sharepoint_url:
        if st.button("Excel von SharePoint laden"):
            df = load_excel_file(sharepoint_url, from_url=True)
            if df is not None:
                st.success("Datei erfolgreich von SharePoint geladen.")

if df is not None:
    # Datenformatanpassungen
    df = df.copy()
    df['Gestartet'] = pd.to_datetime(df['Gestartet'], errors='coerce')
    df['Beendet'] = pd.to_datetime(df['Beendet'], errors='coerce')
    df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce')
    df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce')
    df['Ladezeit_h'] = (df['Beendet'] - df['Gestartet']).dt.total_seconds() / 3600.0
    df['P_Schnitt'] = df['Verbrauch_kWh'] / df['Ladezeit_h']
    df['Jahr'] = df['Beendet'].dt.year
    df['Monat_num'] = df['Beendet'].dt.month
    df['Tag'] = df['Beendet'].dt.day
    df['Stunde'] = df['Beendet'].dt.hour
    df['Monat'] = df['Beendet'].dt.to_period('M').dt.to_timestamp()

    st.subheader("Originaldaten nach Datenformatanpassung")
    st.dataframe(df)

    # 🔁 Einheitliche Farbcodierung:
    colors_auth = px.colors.qualitative.Plotly
    colors_provider = px.colors.qualitative.D3

    auth_types_all = sorted(df['Auth. Typ'].dropna().unique())
    color_map_auth_global = {auth: colors_auth[i % len(colors_auth)] for i, auth in enumerate(auth_types_all)}

    df['Provider_kategorisiert'] = get_top_n_with_rest(df['Provider'], top_n=10)
    providers_all = sorted(df['Provider_kategorisiert'].dropna().unique())
    color_map_provider_global = {prov: colors_provider[i % len(colors_provider)] for i, prov in enumerate(providers_all)}

    # --- Zentrale Filterung: Zeitraum und Standort ---
    st.sidebar.header("Filterung der Auswertungen")

    # Zeitraum-Filter
    min_date = df['Beendet'].min()
    max_date = df['Beendet'].max()
    date_range = st.sidebar.date_input(
        "Zeitraum auswählen",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) != 2:
        st.sidebar.error("Bitte einen gültigen Zeitraum auswählen.")
    else:
        start_date, end_date = date_range

        # Standort-Filter (Mehrfachauswahl möglich)
        standorte = sorted(df['Standortname'].dropna().unique())
        selected_standorte = st.sidebar.multiselect(
            "Standort(e) auswählen",
            options=standorte,
            default=standorte
        )

        # Filterdaten anwenden
        df_filtered = df[
            (df['Beendet'] >= pd.to_datetime(start_date)) &
            (df['Beendet'] <= pd.to_datetime(end_date)) &
            (df['Standortname'].isin(selected_standorte))
        ]

        if df_filtered.empty:
            st.warning("Keine Daten für die gewählte Filterkombination vorhanden.")
        else:
            # Gruppierung und KPIs
            grouped = df_filtered.groupby('Standortname', as_index=False).agg(
                Verbrauch_kWh_sum=('Verbrauch_kWh', 'sum'),
                Verbrauch_kWh_mean=('Verbrauch_kWh', 'mean'),
                Kosten_EUR_sum=('Kosten_EUR', 'sum'),
                Kosten_EUR_mean=('Kosten_EUR', 'mean'),
                P_Schnitt_LV_mean=('P_Schnitt', 'mean'),
                Standzeit_h=('Ladezeit_h', 'mean'),
                Anzahl_Ladevorgaenge=('Verbrauch_kWh', 'count')
            )

            st.subheader("🔢 Allgemeine KPIs nach Standort")
            st.dataframe(grouped, use_container_width=True)

            st.subheader("🌍 Auswertung über das gesamte Portfolio")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("⚡ Verbrauch nach Standort (kWh)")
                fig1 = px.bar(grouped, x="Standortname", y="Verbrauch_kWh_sum", title="Gesamtverbrauch", color="Standortname")
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.subheader("💶 Ladekosten für den User nach Standort (€)")
                fig2 = px.bar(grouped, x="Standortname", y="Kosten_EUR_sum", title="Gesamtkosten", color="Standortname")
                st.plotly_chart(fig2, use_container_width=True)

            portfolio_col1, portfolio_col2 = st.columns(2)

            with portfolio_col1:
                auth_counts_all = df_filtered['Auth. Typ'].value_counts().reset_index()
                auth_counts_all.columns = ['Auth. Typ', 'Anzahl']

                fig_auth_all = px.pie(
                    auth_counts_all,
                    names='Auth. Typ',
                    values='Anzahl',
                    title="🔄 Auth. Typ Verteilung (gesamt)",
                    color='Auth. Typ',
                    color_discrete_map=color_map_auth_global
                )
                st.plotly_chart(fig_auth_all, use_container_width=True)

                auth_trend_all = (
                    df_filtered
                    .groupby([df_filtered['Beendet'].dt.to_period('M'), 'Auth. Typ'])
                    .size()
                    .reset_index(name='Anzahl')
                )
                auth_trend_all['Beendet'] = auth_trend_all['Beendet'].dt.to_timestamp()
                auth_trend_all['Prozent'] = auth_trend_all.groupby('Beendet')['Anzahl'].transform(lambda x: x / x.sum() * 100)

                fig_auth_trend_all = px.bar(
                    auth_trend_all,
                    x="Beendet",
                    y="Prozent",
                    color="Auth. Typ",
                    title="📊 Prozentualer Verlauf der Auth. Typen (gesamt)",
                    color_discrete_map=color_map_auth_global
                )
                fig_auth_trend_all.update_layout(barmode='stack', yaxis_title='Anteil [%]')
                st.plotly_chart(fig_auth_trend_all, use_container_width=True)

            with portfolio_col2:
                provider_counts_all = df_filtered['Provider_kategorisiert'].value_counts().reset_index()
                provider_counts_all.columns = ['Provider', 'Anzahl']

                fig_provider_all = px.pie(
                    provider_counts_all,
                    names='Provider',
                    values='Anzahl',
                    title="🏢 Top 10 Provider + Rest (gesamt)",
                    color='Provider',
                    color_discrete_map=color_map_provider_global
                )
                st.plotly_chart(fig_provider_all, use_container_width=True)

                prov_trend_all = (
                    df_filtered
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
                    color_discrete_map=color_map_provider_global
                )
                fig_prov_trend_all.update_layout(barmode='stack', yaxis_title='Anteil [%]')
                st.plotly_chart(fig_prov_trend_all, use_container_width=True)

            st.subheader("📈 Trendentwicklung ausgewählter KPIs nach Standort")

            # KPI-Auswahl inkl. Anzahl Ladevorgänge
            kpi_auswahl = st.selectbox("🔢 KPI wählen", ['Verbrauch_kWh', 'Kosten_EUR', 'P_Schnitt', 'Ladezeit_h',
                                                        'Anzahl_Ladevorgänge'])
            aggregationsebene = st.selectbox("🗓️ Aggregationsebene", ['Monat', 'Tag', 'Keine Aggregation'])
            aggregationsart = st.selectbox("➗ Aggregationsart", ['Summe', 'Mittelwert'])

            df_trend = df_filtered.copy()

            # Zeitspalte definieren
            if aggregationsebene == 'Monat':
                df_trend['Zeit'] = df_trend['Beendet'].dt.to_period('M').dt.to_timestamp()
            elif aggregationsebene == 'Tag':
                df_trend['Zeit'] = df_trend['Beendet'].dt.date
            else:
                df_trend['Zeit'] = df_trend['Beendet']

            # Berechnung für "Anzahl_Ladevorgänge" (extra Fall, da keine echte Spalte)
            if kpi_auswahl == 'Anzahl_Ladevorgänge':
                if aggregationsebene == 'Keine Aggregation':
                    trend_df = df_trend[['Zeit', 'Standortname']].copy()
                    trend_df['KPI_Wert'] = 1
                else:
                    trend_df = (
                        df_trend
                        .groupby(['Zeit', 'Standortname'])
                        .size()
                        .reset_index(name='KPI_Wert')
                    )
            else:
                # Andere KPIs wie gewohnt
                if aggregationsebene == 'Keine Aggregation':
                    trend_df = df_trend[['Zeit', 'Standortname', kpi_auswahl]].rename(columns={kpi_auswahl: 'KPI_Wert'})
                else:
                    agg_func = 'sum' if aggregationsart == 'Summe' else 'mean'
                    trend_df = (
                        df_trend
                        .groupby(['Zeit', 'Standortname'])
                        .agg(KPI_Wert=(kpi_auswahl, agg_func))
                        .reset_index()
                    )

            # Trendplot nach Standort
            fig_kpi_trend = px.line(
                trend_df,
                x='Zeit',
                y='KPI_Wert',
                color='Standortname',
                markers=True,
                title=f'📉 Verlauf von "{kpi_auswahl}" ({aggregationsart}) nach Standort',
                labels={'Zeit': 'Zeit', 'KPI_Wert': kpi_auswahl}
            )
            fig_kpi_trend.update_layout(xaxis_title="Zeit", yaxis_title=kpi_auswahl)
            st.plotly_chart(fig_kpi_trend, use_container_width=True)

            # 🔄 KUMULIERTER Verlauf (nur Summe sinnvoll)
            st.subheader(f"📊 Kumulierte Entwicklung von '{kpi_auswahl}' über alle Standorte")

            if kpi_auswahl == 'Anzahl_Ladevorgänge':
                if aggregationsebene == 'Keine Aggregation':
                    df_kumuliert = df_trend[['Zeit']].copy()
                    df_kumuliert['KPI_Wert'] = 1
                else:
                    df_kumuliert = (
                        df_trend
                        .groupby('Zeit')
                        .size()
                        .reset_index(name='KPI_Wert')
                    )
            else:
                if aggregationsebene == 'Keine Aggregation':
                    df_kumuliert = df_trend[['Zeit', kpi_auswahl]].rename(columns={kpi_auswahl: 'KPI_Wert'}).copy()
                else:
                    df_kumuliert = (
                        df_trend
                        .groupby('Zeit')
                        .agg(KPI_Wert=(kpi_auswahl, 'sum' if aggregationsart == 'Summe' else 'mean'))
                        .reset_index()
                    )

            # Kumulieren
            df_kumuliert = df_kumuliert.sort_values(by='Zeit')
            df_kumuliert['KPI_Kumuliert'] = df_kumuliert['KPI_Wert'].cumsum()

            # Plot kumuliert
            fig_kpi_kumuliert = px.line(
                df_kumuliert,
                x='Zeit',
                y='KPI_Kumuliert',
                title=f'📈 Kumulierte Entwicklung von "{kpi_auswahl}" ({aggregationsart})',
                labels={'KPI_Kumuliert': f'Kumuliert: {kpi_auswahl}', 'Zeit': 'Zeit'}
            )
            st.plotly_chart(fig_kpi_kumuliert, use_container_width=True)


            st.subheader("📊 Detaillierte Auswertung pro Standort")

            for standort in selected_standorte:
                st.markdown(f"### 📍 {standort}")
                df_standort = df_filtered[df_filtered['Standortname'] == standort].copy()

                # Verbrauch pro Monat
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
                    color_continuous_scale='Cividis'
                )
                st.plotly_chart(fig_sum_monat, use_container_width=True)

                auth_col, prov_col = st.columns(2)

                with auth_col:
                    auth_counts = df_standort['Auth. Typ'].value_counts().reset_index()
                    auth_counts.columns = ['Auth. Typ', 'Anzahl']

                    fig_auth = px.pie(
                        auth_counts,
                        names='Auth. Typ',
                        values='Anzahl',
                        title="🔄 Auth. Typ Verteilung",
                        color='Auth. Typ',
                        color_discrete_map=color_map_auth_global
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
                        color_discrete_map=color_map_auth_global
                    )
                    fig_auth_trend.update_layout(barmode='stack', yaxis_title='Anteil [%]')
                    st.plotly_chart(fig_auth_trend, use_container_width=True)

                with prov_col:
                    df_standort['Provider_kategorisiert'] = get_top_n_with_rest(df_standort['Provider'], top_n=10)
                    provider_counts = df_standort['Provider_kategorisiert'].value_counts().reset_index()
                    provider_counts.columns = ['Provider', 'Anzahl']

                    fig_provider = px.pie(
                        provider_counts,
                        names='Provider',
                        values='Anzahl',
                        title="🏢 Top 10 Provider + Rest",
                        color='Provider',
                        color_discrete_map=color_map_provider_global
                    )
                    st.plotly_chart(fig_provider, use_container_width=True)

                    prov_trend = (
                        df_standort
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
                        color_discrete_map=color_map_provider_global
                    )
                    fig_prov_trend.update_layout(barmode='stack', yaxis_title='Anteil [%]')
                    st.plotly_chart(fig_prov_trend, use_container_width=True)
