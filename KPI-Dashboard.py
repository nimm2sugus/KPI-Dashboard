# Ladeanalyse Dashboard - komplett überarbeitetes Skript

import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request

# ------------------- Seite konfigurieren -------------------
st.set_page_config(page_title="Ladeanalyse Dashboard", layout="wide")
st.title("🔌 Ladeanalyse Dashboard")

# ------------------- Hilfsfunktionen -------------------
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

def prepare_dataframe(df):
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
    df['Provider_kategorisiert'] = get_top_n_with_rest(df['Provider'], top_n=10)
    return df

# ------------------- Datenquelle auswählen -------------------
input_method = st.radio("📂 Datenquelle wählen:", ["Datei-Upload", "SharePoint-Link"])
df = None

if input_method == "Datei-Upload":
    uploaded_file = st.file_uploader("📁 Excel-Datei hochladen", type=["xlsx", "xls"])
    if uploaded_file:
        df = load_excel_file(uploaded_file)
elif input_method == "SharePoint-Link":
    sharepoint_url = st.text_input("🔗 SharePoint-Download-Link")
    if sharepoint_url and st.button("Laden"):
        df = load_excel_file(sharepoint_url, from_url=True)

# ------------------- Datenprüfung und Vorverarbeitung -------------------
if df is not None:
    df = prepare_dataframe(df)

    invalid_dates = df[df['Gestartet'].isna() | df['Beendet'].isna()]
    if not invalid_dates.empty:
        st.warning(f"{len(invalid_dates)} Zeilen mit ungültigen Datumswerten wurden ignoriert.")
        st.dataframe(invalid_dates)

    st.subheader("🔢 Daten (Vorverarbeitet)")
    st.dataframe(df)

    # ------------------- Farben -------------------
    color_map_auth = {k: v for k, v in zip(df['Auth. Typ'].dropna().unique(), px.colors.qualitative.Plotly)}
    color_map_provider = {k: v for k, v in zip(df['Provider_kategorisiert'].dropna().unique(), px.colors.qualitative.D3)}

    # ------------------- Filter -------------------
    st.sidebar.header("🔎 Filter")
    min_d, max_d = df['Beendet'].min(), df['Beendet'].max()
    date_range = st.sidebar.date_input("Zeitraum", value=(min_d, max_d), min_value=min_d, max_value=max_d)

    standorte = sorted(df['Standortname'].dropna().unique())
    selected_standorte = st.sidebar.multiselect("Standorte", standorte, default=standorte)

    df_filtered = df[(df['Beendet'] >= pd.to_datetime(date_range[0])) &
                     (df['Beendet'] <= pd.to_datetime(date_range[1])) &
                     (df['Standortname'].isin(selected_standorte))]

    if df_filtered.empty:
        st.warning("Keine Daten für diese Filterkombination.")
        st.stop()

    # ------------------- KPIs -------------------
    st.subheader("📊 KPIs nach Standort")
    grouped = df_filtered.groupby('Standortname').agg({
        'Verbrauch_kWh': ['sum', 'mean'],
        'Kosten_EUR': ['sum', 'mean'],
        'P_Schnitt': 'mean',
        'Ladezeit_h': 'mean',
        'Verbrauch (kWh)': 'count'
    })
    grouped.columns = ['Verbrauch_sum', 'Verbrauch_avg', 'Kosten_sum', 'Kosten_avg', 'P_avg', 'Ladezeit_avg', 'Ladevorgange']
    st.dataframe(grouped.reset_index())

    # ------------------- Visualisierungen -------------------
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.bar(grouped.reset_index(), x='Standortname', y='Verbrauch_sum', color='Standortname',
                               title="⚡ Verbrauch (kWh)"), use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(grouped.reset_index(), x='Standortname', y='Kosten_sum', color='Standortname',
                               title="💶 Kosten (€)"), use_container_width=True)

    # ------------------- Trendentwicklung -------------------
    st.subheader("📈 Trendentwicklung KPIs")

    kpi = st.selectbox("KPI", ['Verbrauch_kWh', 'Kosten_EUR', 'P_Schnitt', 'Ladezeit_h'])
    agg_level = st.selectbox("Aggregationsebene", ['Monat', 'Tag'])

    df_filtered['Zeit'] = df_filtered['Beendet'].dt.to_period('M' if agg_level == 'Monat' else 'D').dt.to_timestamp()

    trend_df = df_filtered.groupby(['Zeit', 'Standortname']).agg({kpi: 'mean'}).reset_index()

    fig_trend = px.line(trend_df, x='Zeit', y=kpi, color='Standortname', markers=True,
                        title=f"{kpi} im Zeitverlauf")
    st.plotly_chart(fig_trend, use_container_width=True)

    # ------------------- Auth. Typ Verteilung -------------------
    st.subheader("🛋️ Authentifizierungstypen")
    auth_counts = df_filtered['Auth. Typ'].value_counts().reset_index()
    auth_counts.columns = ['Auth. Typ', 'Anzahl']

    fig_auth = px.pie(auth_counts, names='Auth. Typ', values='Anzahl', color='Auth. Typ',
                      color_discrete_map=color_map_auth)
    st.plotly_chart(fig_auth, use_container_width=True)

    # ------------------- Provider Verteilung -------------------
    st.subheader("🏢 Provider")
    provider_counts = df_filtered['Provider_kategorisiert'].value_counts().reset_index()
    provider_counts.columns = ['Provider', 'Anzahl']

    fig_prov = px.pie(provider_counts, names='Provider', values='Anzahl', color='Provider',
                      color_discrete_map=color_map_provider)
    st.plotly_chart(fig_prov, use_container_width=True)
