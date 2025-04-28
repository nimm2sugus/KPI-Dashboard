pie_col1, line_col1 = st.columns(2)

# --- Pie Chart Auth Typ ---
with pie_col1:
    auth_counts = df_standort['Auth. Typ'].value_counts().reset_index()
    auth_counts.columns = ['Auth. Typ', 'Anzahl']

    # Farbpalette für Auth Typ
    colors_auth = px.colors.qualitative.Plotly  # Palette 1
    # Sortiere die Auth-Typen alphabetisch
    unique_auth_types = sorted(auth_counts['Auth. Typ'].tolist())
    color_map_auth = {auth_type: colors_auth[i % len(colors_auth)] for i, auth_type in enumerate(unique_auth_types)}

    fig_auth = px.pie(
        auth_counts,
        names='Auth. Typ',
        values='Anzahl',
        title="Auth. Typ Verteilung",
        color='Auth. Typ',  # Dies stellt sicher, dass die Farben korrekt zugewiesen werden
        color_discrete_map=color_map_auth  # Farbzuordnung für das Pie-Chart
    )
    st.plotly_chart(fig_auth, use_container_width=True)

# --- Line Chart Auth Typ Verlauf ---
with line_col1:
    auth_trend = (
        df_standort
        .groupby([df_standort['Beendet'].dt.to_period('M'), 'Auth. Typ'])
        .size()
        .reset_index(name='Anzahl')
    )
    auth_trend['Beendet'] = auth_trend['Beendet'].dt.to_timestamp()

    # Sortiere die Auth-Typen alphabetisch für die konsistente Farbzuordnung
    # Verwende die bereits definierte color_map_auth
    fig_auth_trend = px.line(
        auth_trend,
        x="Beendet",
        y="Anzahl",
        color="Auth. Typ",
        markers=True,
        title="📈 Verlauf der Auth. Typen im Zeitverlauf",
        color_discrete_map=color_map_auth  # Die gleiche Farbzuordnung wie im Pie-Chart
    )
    st.plotly_chart(fig_auth_trend, use_container_width=True)

# -------------------------------------------------------------------

pie_col2, line_col2 = st.columns(2)

# --- Pie Chart Provider ---
with pie_col2:
    df_standort_copy = df_standort.copy()
    df_standort_copy['Provider_kategorisiert'] = get_top_n_with_rest(df_standort_copy['Provider'], top_n=10)

    provider_counts = df_standort_copy.groupby('Provider_kategorisiert').size().reset_index(name='Anzahl')
    provider_counts = provider_counts.rename(columns={'Provider_kategorisiert': 'Provider'})

    # Farbpalette für Provider (eine andere als oben!)
    colors_provider = px.colors.qualitative.D3  # Palette 2
    # Sortiere die Provider alphabetisch
    unique_providers = sorted(provider_counts['Provider'].tolist())
    color_map_provider = {provider: colors_provider[i % len(colors_provider)] for i, provider in enumerate(unique_providers)}

    fig_provider = px.pie(
        provider_counts,
        names='Provider',
        values='Anzahl',
        title="Top 10 Provider + Rest",
        color='Provider',  # Dies stellt sicher, dass die Farben korrekt zugewiesen werden
        color_discrete_map=color_map_provider  # Farbzuordnung für das Pie-Chart
    )
    st.plotly_chart(fig_provider, use_container_width=True)

# --- Line Chart Provider Verlauf ---
with line_col2:
    df_standort_copy['Monat'] = df_standort_copy['Beendet'].dt.to_period('M').dt.to_timestamp()

    prov_trend = (
        df_standort_copy
        .groupby(['Monat', 'Provider_kategorisiert'])
        .size()
        .reset_index(name='Anzahl')
    )

    # Sortiere die Provider alphabetisch für die konsistente Farbzuordnung
    # Verwende die bereits definierte color_map_provider
    fig_prov_trend = px.line(
        prov_trend,
        x="Monat",
        y="Anzahl",
        color="Provider_kategorisiert",
        markers=True,
        title="📈 Verlauf der Provider (Top 10 + Rest)",
        color_discrete_map=color_map_provider  # Die gleiche Farbzuordnung wie im Pie-Chart
    )
    st.plotly_chart(fig_prov_trend, use_container_width=True)
