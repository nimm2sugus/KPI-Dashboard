# Ladeanalyse-Dashboard (Streamlit)

import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request

# Seitenlayout
st.set_page_config(page_title="Ladevorgangs-Daten", layout="wide")

# --- Funktionen ---

@st.cache_data
def load_excel_file(source, from_url=False):
    """Lädt eine Excel-Datei lokal oder über URL."""
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
    """Behalte nur die Top-N häufigsten Werte, Rest wird zu 'Rest' zusammengefasst."""
    top_values = series.value_counts().nlargest(top_n).index
    return series.where(series.isin(top_values), other='Rest')

# --- Hauptprogramm ---

st.title("🔌 Ladeanalyse Dashboard")

# Eingabemethode
input_method = st.radio("📂 Datenquelle wählen:", ["Datei-Upload", "SharePoint-Link"])

df = None
selected_standorte = []

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

# Wenn Daten geladen wurden:
if df is not None:
    df = df.copy()

    # Erwartete Spalten prüfen
    expected_cols = ['Gestartet', 'Beendet', 'Verbrauch (kWh)', 'Kosten', 'Auth. Typ', 'Provider', 'Standortname']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Fehlende erforderliche Spalten in der Datei: {missing_cols}")
        st.stop()

    # Datumsformat prüfen & konvertieren
    df['Gestartet'] = pd.to_datetime(df['Gestartet'], errors='coerce')
    df['Beendet'] = pd.to_datetime(df['Beendet'], errors='coerce')

    # Ungültige Datumszeilen anzeigen
    invalid_dates = df[df['Gestartet'].isna() | df['Beendet'].isna()]
    if not invalid_dates.empty:
        st.warning(f"⚠️ {len(invalid_dates)} Zeilen mit ungültigem Datum wurden ignoriert.")
        st.dataframe(invalid_dates)

    # Nur gültige Zeilen weiterverwenden
    df = df.dropna(subset=['Gestartet', 'Beendet'])

    # Umbenennen + Konvertierung numerischer Spalten
    df['Verbrauch_kWh'] = pd.to_numeric(df['Verbrauch (kWh)'], errors='coerce').fillna(0)
    df['Kosten_EUR'] = pd.to_numeric(df['Kosten'], errors='coerce').fillna(0)

    # Ladezeit berechnen (in Stunden)
    df['Ladezeit_h'] = (df['Beendet'] - df['Gestartet']).dt.total_seconds() / 3600
    df = df[df['Ladezeit_h'] > 0]

    # Durchschnittliche Ladeleistung (P = E / t)
    df['P_Schnitt'] = df.apply(
        lambda row: row['Verbrauch_kWh'] / row['Ladezeit_h'] if row['Ladezeit_h'] > 0 else 0,
        axis=1
    )

    # Zeitspalten extrahieren
    df['Jahr'] = df['Beendet'].dt.year
    df['Monat'] = df['Beendet'].dt.to_period('M').dt.to_timestamp()
    df['Tag'] = df['Beendet'].dt.date
    df['Stunde'] = df['Beendet'].dt.hour

    # Providerkategorisierung
    df['Provider_kategorisiert'] = get_top_n_with_rest(df['Provider'], top_n=10)

    # --- Sidebar Filter ---
    st.sidebar.header("Filter")

    # Zeitraum-Filter
    min_date = df['Beendet'].min().date()
    max_date = df['Beendet'].max().date()
    date_range = st.sidebar.date_input("Zeitraum auswählen", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    # Standortfilter (optimiert)
    standorte = sorted(df['Standortname'].dropna().unique())
    selected_standorte = st.sidebar.multiselect(
        "📍 Standort(e) auswählen",
        options=standorte,
        default=standorte,
        help="Wähle einen oder mehrere Standorte aus."
    )

    # Prüfung des Zeitraums
    if len(date_range) != 2:
        st.sidebar.error("Bitte einen gültigen Zeitraum auswählen.")
        st.stop()

    start_date, end_date = date_range
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

    # --- Kennzahlen-Berechnung ---
    grouped = df_filtered.groupby('Standortname', as_index=False).agg(
        Verbrauch_kWh_sum=('Verbrauch_kWh', 'sum'),
        Verbrauch_kWh_mean=('Verbrauch_kWh', 'mean'),
        Kosten_EUR_sum=('Kosten_EUR', 'sum'),
        Kosten_EUR_mean=('Kosten_EUR', 'mean'),
        P_Schnitt_mean=('P_Schnitt', 'mean'),
        Ladezeit_h_mean=('Ladezeit_h', 'mean'),
        Anzahl_Ladevorgaenge=('Verbrauch_kWh', 'count')
    )

    # Tabelle anzeigen
    rows = grouped.shape[0]
    row_height = 35
    max_height = 800
    calculated_height = min(max_height, rows * row_height)
    st.subheader("🔢 Allgemeine KPIs nach Standort")
    st.dataframe(grouped, use_container_width=True, height=calculated_height)

    # Farben für Plotly
    colors_auth = px.colors.qualitative.Plotly
    colors_provider = px.colors.qualitative.D3

    auth_types = sorted(df_filtered['Auth. Typ'].dropna().unique())
    color_map_auth = {auth: colors_auth[i % len(colors_auth)] for i, auth in enumerate(auth_types)}

    providers = sorted(df_filtered['Provider_kategorisiert'].dropna().unique())
    color_map_provider = {prov: colors_provider[i % len(colors_provider)] for i, prov in enumerate(providers)}

    # --- Portfolio-Übersicht ---
    st.subheader("🌍 Portfolio-Übersicht")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚡ Verbrauch nach Standort (kWh)")
        fig1 = px.bar(grouped, x="Standortname", y="Verbrauch_kWh_sum", color="Standortname")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("💶 Ladekosten nach Standort (€)")
        fig2 = px.bar(grouped, x="Standortname", y="Kosten_EUR_sum", color="Standortname")
        st.plotly_chart(fig2, use_container_width=True)

    # Torten für Auth und Provider
    auth_counts = df_filtered['Auth. Typ'].value_counts().reset_index()
    auth_counts.columns = ['Auth. Typ', 'Anzahl']
    fig_auth = px.pie(auth_counts, names='Auth. Typ', values='Anzahl', title="🔄 Auth. Typ Verteilung (gesamt)", color='Auth. Typ', color_discrete_map=color_map_auth)
    st.plotly_chart(fig_auth, use_container_width=True)

    prov_counts = df_filtered['Provider_kategorisiert'].value_counts().reset_index()
    prov_counts.columns = ['Provider', 'Anzahl']
    fig_prov = px.pie(prov_counts, names='Provider', values='Anzahl', title="🏢 Top 10 Provider + Rest (gesamt)", color='Provider', color_discrete_map=color_map_provider)
    st.plotly_chart(fig_prov, use_container_width=True)

    # --- Trendentwicklung ---
    st.subheader("📈 Trendentwicklung ausgewählter KPIs")

    kpi_option = st.selectbox("KPI auswählen", ['Verbrauch_kWh', 'Kosten_EUR', 'P_Schnitt', 'Ladezeit_h', 'Anzahl_Ladevorgaenge'])

    agg_level = st.selectbox("Aggregationsebene", ['Monat', 'Tag', 'Keine Aggregation'])

    # Aggregationsart fest auf Summe gesetzt
    agg_method = 'sum'

    # Checkbox für Gesamtlinie einblenden
    zeige_gesamt = st.checkbox("➕ Gesamtlinie einblenden", value=True)

    # Zeitachse erstellen
    df_trend = df_filtered.copy()

    if agg_level == 'Monat':
        df_trend['Zeit'] = df_trend['Beendet'].dt.to_period('M').dt.to_timestamp()
    elif agg_level == 'Tag':
        df_trend['Zeit'] = df_trend['Beendet'].dt.date
    else:
        df_trend['Zeit'] = df_trend['Beendet']

    # KPI-Werte berechnen
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
            trend_df = df_trend.groupby(['Zeit', 'Standortname']).agg(KPI_Wert=(kpi_option, 'sum')).reset_index()

    # Gesamtlinie nur wenn Checkbox aktiv und keine 'Keine Aggregation'
    if zeige_gesamt and agg_level != 'Keine Aggregation':
        gesamt_df = trend_df.groupby('Zeit', as_index=False)['KPI_Wert'].sum()
        gesamt_df['Standortname'] = 'Gesamtportfolio (basierend auf Standortauswahl)'
        trend_df = pd.concat([trend_df, gesamt_df], ignore_index=True)

    # Liniendiagramm mit horizontaler Legende
    fig_trend = px.line(
        trend_df,
        x='Zeit',
        y='KPI_Wert',
        color='Standortname',
        markers=True,
        title=f'📉 Verlauf von {kpi_option} (Summe) nach Standort',
        labels={'KPI_Wert': kpi_option, 'Zeit': 'Zeit'}
    )
    fig_trend.update_layout(
        legend=dict(
            orientation="v",  # Vertikale Legende
            x=1.02,  # Rechts außerhalb des Plots
            y=1,  # Oben ausgerichtet
            xanchor="left",
            yanchor="top",
            title="Ausgewählte Standorte",
            font=dict(
                size=12
            ),
        ),
        margin=dict(r=150)  # Platz rechts schaffen, damit Legende nicht abgeschnitten wird
    )

    # Optional: Farblich hervorheben Gesamtlinie
    for trace in fig_trend.data:
        if trace.name == 'Gesamtportfolio (basierend auf Standortauswahl)':
            trace.update(line=dict(color='gold', width=3, dash='dash'))  # deutlichere Linie
        else:
            trace.update(line=dict(width=2))

    # Anzeige
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Detaillierte Auswertung je Standort ---
    st.subheader("📊 Detaillierte Auswertung pro Standort")

    for standort in selected_standorte:
        with st.expander(f"📍 {standort}", expanded=False):
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
                                       color='Auth. Typ', color_discrete_map=color_map_auth)
            st.plotly_chart(fig_auth_standort, use_container_width=True)
            
            # Provider Verteilung für Standort
            prov_counts_standort = df_standort['Provider_kategorisiert'].value_counts().reset_index()
            prov_counts_standort.columns = ['Provider', 'Anzahl']
            fig_prov_standort = px.pie(prov_counts_standort, names='Provider', values='Anzahl', 
                                       title="🏢 Top 10 Provider + Rest (gesamt)", color='Provider', 
                                       color_discrete_map=color_map_provider)
            st.plotly_chart(fig_prov_standort, use_container_width=True)

else:
    st.info("Bitte lade eine bereinigte Excel-Datei hoch oder gib einen SharePoint-Link ein, um die Analyse zu starten.")
