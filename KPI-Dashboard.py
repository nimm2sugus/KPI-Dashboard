import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request

# --- Seitenkonfiguration ---
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")

# --- Funktion zum Laden der Excel-Datei mit Cache ---
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

# --- Hilfsfunktion: Top N Werte mit "Rest" zusammenfassen ---
def get_top_n_with_rest(series, top_n=10):
    # Top N häufigste Werte beibehalten, alle anderen als 'Rest' markieren
    top_values = series.value_counts().nlargest(top_n).index
    return series.where(series.isin(top_values), other='Rest')

# --- App-Titel ---
st.title("🔌 Ladeanalyse Dashboard")

# --- Datenquelle wählen ---
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

# --- Wenn Daten geladen ---
if df is not None:
    # --- Datenvorbereitung ---
    df = df.copy()

    # --- Erforderliche Spalten prüfen ---
    expected_cols = ['Gestartet', 'Beendet', 'Verbrauch (kWh)', 'Kosten', 'Auth. Typ', 'Provider', 'Standortname']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Fehlende erforderliche Spalten in der Datei: {missing_cols}")
        st.stop()

    # --- Datumsfelder parsen ---
    df['Gestartet'] = pd.to_datetime(df['Gestartet'], errors='coerce')
    df['Beendet'] = pd.to_datetime(df['Beendet'], errors='coerce')

    # Warnung bei ungültigen Datumswerten (wird hier vor Filtern angezeigt)
    invalid_dates = df[df['Gestartet'].isna() | df['Beendet'].isna()]
    if not invalid_dates.empty:
        st.warning(f"⚠️ {len(invalid_dates)} Zeilen mit ungültigem Datum wurden ignoriert.")
        st.dataframe(invalid_dates)

    # Ungültige Datumswerte entfernen
    df = df.dropna(subset=['Gestartet', 'Beendet'])

    # --- Numerische Felder konvertieren ---
    df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce').fillna(0)
    df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce').fillna(0)

    # --- Ladezeit in Stunden berechnen, negative oder 0 Zeit entfernen ---
    df['Ladezeit_h'] = (df['Beendet'] - df['Gestartet']).dt.total_seconds() / 3600
    df = df[df['Ladezeit_h'] > 0]

    # --- Leistungs-Schnitt berechnen (kW), Absicherung gegen Division durch 0 ---
    df['P_Schnitt'] = df.apply(
        lambda row: row['Verbrauch_kWh'] / row['Ladezeit_h'] if row['Ladezeit_h'] > 0 else 0,
        axis=1
    )

    # --- Weitere Zeitspalten ---
    df['Jahr'] = df['Beendet'].dt.year
    df['Monat'] = df['Beendet'].dt.to_period('M').dt.to_timestamp()
    df['Tag'] = df['Beendet'].dt.date
    df['Stunde'] = df['Beendet'].dt.hour

    # --- Provider kategorisieren (Top 10 + Rest) ---
    df['Provider_kategorisiert'] = get_top_n_with_rest(df['Provider'], top_n=10)

    # --- Sidebar: Filter ---
    st.sidebar.header("Filter")

    min_date = df['Beendet'].min().date()
    max_date = df['Beendet'].max().date()

    date_range = st.sidebar.date_input(
        "Zeitraum auswählen",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Standortfilter
    standorte = sorted(df['Standortname'].dropna().unique())
    selected_standorte = st.sidebar.multiselect("Standort(e) auswählen", options=standorte, default=standorte)

    # Filter prüfen
    if len(date_range) != 2:
        st.sidebar.error("Bitte einen gültigen Zeitraum auswählen.")
        st.stop()

    start_date, end_date = date_range

    # Enddatum auf 23:59:59 setzen, um den ganzen Tag zu erfassen
    end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    # Filter anwenden
    df_filtered = df[
        (df['Beendet'] >= pd.to_datetime(start_date)) &
        (df['Beendet'] <= end_date) &
        (df['Standortname'].isin(selected_standorte))
    ]

    if df_filtered.empty:
        st.warning("Keine Daten für die gewählte Filterkombination vorhanden.")
        st.stop()

    # --- KPIs nach Standort ---
    grouped = df_filtered.groupby('Standortname', as_index=False).agg(
        Verbrauch_kWh_sum=('Verbrauch_kWh', 'sum'),
        Verbrauch_kWh_mean=('Verbrauch_kWh', 'mean'),
        Kosten_EUR_sum=('Kosten_EUR', 'sum'),
        Kosten_EUR_mean=('Kosten_EUR', 'mean'),
        P_Schnitt_mean=('P_Schnitt', 'mean'),
        Ladezeit_h_mean=('Ladezeit_h', 'mean'),
        Anzahl_Ladevorgaenge=('Verbrauch_kWh', 'count')
    )

    st.subheader("🔢 Allgemeine KPIs nach Standort")
    st.dataframe(grouped, use_container_width=True)

    # --- Farbzuordnungen ---
    colors_auth = px.colors.qualitative.Plotly
    colors_provider = px.colors.qualitative.D3

    auth_types = sorted(df_filtered['Auth. Typ'].dropna().unique())
    color_map_auth = {auth: colors_auth[i % len(colors_auth)] for i, auth in enumerate(auth_types)}

    providers = sorted(df_filtered['Provider_kategorisiert'].dropna().unique())
    color_map_provider = {prov: colors_provider[i % len(colors_provider)] for i, prov in enumerate(providers)}

    # --- Portfolio-Auswertungen ---
    st.subheader("🌍 Portfolio-Übersicht")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚡ Verbrauch nach Standort (kWh)")
        fig1 = px.bar(grouped, x="Standortname", y="Verbrauch_kWh_sum", color="Standortname",
                      labels={"Verbrauch_kWh_sum": "Gesamtverbrauch (kWh)", "Standortname": "Standort"})
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("💶 Ladekosten nach Standort (€)")
        fig2 = px.bar(grouped, x="Standortname", y="Kosten_EUR_sum", color="Standortname",
                      labels={"Kosten_EUR_sum": "Gesamtkosten (€)", "Standortname": "Standort"})
        st.plotly_chart(fig2, use_container_width=True)

    # Auth. Typ Verteilung gesamt
    auth_counts = df_filtered['Auth. Typ'].value_counts().reset_index()
    auth_counts.columns = ['Auth. Typ', 'Anzahl']

    fig_auth = px.pie(auth_counts, names='Auth. Typ', values='Anzahl',
                      title="🔄 Auth. Typ Verteilung (gesamt)",
                      color='Auth. Typ',
                      color_discrete_map=color_map_auth)
    st.plotly_chart(fig_auth, use_container_width=True)

    # Provider Verteilung gesamt
    prov_counts = df_filtered['Provider_kategorisiert'].value_counts().reset_index()
    prov_counts.columns = ['Provider', 'Anzahl']

    fig_prov = px.pie(prov_counts, names='Provider', values='Anzahl',
                      title="🏢 Top 10 Provider + Rest (gesamt)",
                      color='Provider',
                      color_discrete_map=color_map_provider)
    st.plotly_chart(fig_prov, use_container_width=True)

    # --- Trenddarstellung ---
    st.subheader("📈 Trendentwicklung ausgewählter KPIs")

    # KPI Auswahl
    kpi_option = st.selectbox("KPI auswählen",
                              ['Verbrauch_kWh', 'Kosten_EUR', 'P_Schnitt', 'Ladezeit_h', 'Anzahl_Ladevorgaenge'])

    # Aggregationsebene
    agg_level = st.selectbox("Aggregationsebene", ['Monat', 'Tag', 'Keine Aggregation'])

    # Aggregationsart
    agg_method = st.selectbox("Aggregationsart", ['Summe', 'Mittelwert'])

    df_trend = df_filtered.copy()

    # Zeitspalte für Aggregation
    if agg_level == 'Monat':
        df_trend['Zeit'] = df_trend['Beendet'].dt.to_period('M').dt.to_timestamp()
    elif agg_level == 'Tag':
        df_trend['Zeit'] = df_trend['Beendet'].dt.date
    else:
        df_trend['Zeit'] = df_trend['Beendet']

    # KPI-Wert berechnen
    if kpi_option == 'Anzahl_Ladevorgaenge':
        if agg_level == 'Keine Aggregation':
            trend_df = df_trend[['Zeit', 'Standortname']].copy()
            trend_df['KPI_Wert'] = 1
        else:
            trend_df = df_trend.groupby(['Zeit', 'Standortname']).size().reset_index(name='KPI_Wert')
    else:
        if agg_level == 'Keine Aggregation':
            trend_df = df_trend[['Zeit', 'Standortname', kpi_option]].rename(columns={kpi_option: 'KPI_Wert'})
        else:
            func = 'sum' if agg_method == 'Summe' else 'mean'
            trend_df = df_trend.groupby(['Zeit', 'Standortname']).agg(KPI_Wert=(kpi_option, func)).reset_index()

    # KPI-Trend nach Standort plotten
    fig_trend = px.line(trend_df, x='Zeit', y='KPI_Wert', color='Standortname',
                        markers=True,
                        title=f'📉 Verlauf von {kpi_option} ({agg_method}) nach Standort',
                        labels={'KPI_Wert': kpi_option, 'Zeit': 'Zeit'})
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Kumulierte Entwicklung ---
    st.subheader(f"📊 Kumulierte Entwicklung von '{kpi_option}'")

    if kpi_option == 'Anzahl_Ladevorgaenge':
        if agg_level == 'Keine Aggregation':
            df_cum = df_trend[['Zeit']].copy()
            df_cum['KPI_Wert'] = 1
        else:
            df_cum = df_trend.groupby('Zeit').size().reset_index(name='KPI_Wert')
    else:
        if agg_level == 'Keine Aggregation':
            df_cum = df_trend[['Zeit', kpi_option]].rename(columns={kpi_option: 'KPI_Wert'}).copy()
        else:
            func = 'sum' if agg_method == 'Summe' else 'mean'
            df_cum = df_trend.groupby('Zeit').agg(KPI_Wert=(kpi_option, func)).reset_index()

    # Kumulieren (aufsteigend sortieren)
    df_cum = df_cum.sort_values('Zeit')
    df_cum['KPI_Kumuliert'] = df_cum['KPI_Wert'].cumsum()

    fig_cum = px.line(df_cum, x='Zeit', y='KPI_Kumuliert',
                      title=f'📈 Kumulierte Entwicklung von {kpi_option} ({agg_method})',
                      labels={'KPI_Kumuliert': f'Kumuliert: {kpi_option}', 'Zeit': 'Zeit'})
    st.plotly_chart(fig_cum, use_container_width=True)

    # --- Detaillierte Auswertung je Standort ---
    st.subheader("📊 Detaillierte Auswertung pro Standort")

    for standort in selected_standorte:
        st.markdown(f"### 📍 {standort}")

        df_standort = df_filtered[df_filtered['Standortname'] == standort].copy()

        # Verbrauch pro Monat
        verbrauch_monat = df_standort.groupby(df_standort['Beendet'].dt.to_period('M')).agg(
            Gesamtverbrauch_kWh=('Verbrauch_kWh', 'sum')
        ).reset_index()
        verbrauch_monat['Monat'] = verbrauch_monat['Beendet'].dt.to_timestamp()

        fig_verbrauch_monat = px.bar(verbrauch_monat, x='Monat', y='Gesamtverbrauch_kWh',
                                    title=f'Gesamtverbrauch pro Monat - {standort}',
                                    labels={'Gesamtverbrauch_kWh': 'Verbrauch (kWh)', 'Monat': 'Monat'})
        st.plotly_chart(fig_verbrauch_monat, use_container_width=True)

        # Auth. Typ Verteilung für Standort
        auth_counts_standort = df_standort['Auth. Typ'].value_counts().reset_index()
        auth_counts_standort.columns = ['Auth. Typ', 'Anzahl']

        fig_auth_standort = px.pie(auth_counts_standort, names='Auth. Typ', values='Anzahl',
                                  title=f"Auth. Typ Verteilung - {standort}",
                                  color='Auth. Typ',
                                  color_discrete_map=color_map_auth)
        st.plotly_chart(fig_auth_standort, use_container_width=True)

        # Provider Verteilung für Standort
        prov_counts_standort = df_standort['Provider_kategorisiert'].value_counts().reset_index()
        prov_counts_standort.columns = ['Provider', 'Anzahl']

        fig_prov_standort = px.pie(prov_counts_standort, names='Provider', values='Anzahl',
                                  title=f"Provider Verteilung - {standort}",
                                  color='Provider',
                                  color_discrete_map=color_map_provider)
        st.plotly_chart(fig_prov_standort, use_container_width=True)
