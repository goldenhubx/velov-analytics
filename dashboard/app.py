"""Dashboard qualité/temps réel du réseau Vélo'v."""

import os

import duckdb
import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(page_title="Vélo'v — Qualité & état du réseau", layout="wide")

STATUS_COLORS = {
    "ok": [34, 197, 94],
    "dormant": [59, 130, 246],
    "closed_but_reporting": [245, 158, 11],
    "silent_while_operational": [239, 68, 68],
    "constant_gap": [168, 85, 247],
}

STATUS_LABELS = {
    "ok": "OK — aucune anomalie détectée",
    "dormant": "Dormante — aucun rapport depuis plus de 7 jours",
    "closed_but_reporting": "Fermée mais active — station arrêtée qui continue de rapporter (ex. travaux)",
    "silent_while_operational": "Muette — se déclare active mais tous les compteurs sont à zéro",
    "constant_gap": "Écart figé — écart de capacité identique sur toutes les mesures opérationnelles",
}


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    token = os.environ["MOTHERDUCK_TOKEN_READONLY"]
    return duckdb.connect(
        f"md:velov_analytics?motherduck_token={token}", read_only=True
    )


@st.cache_data(ttl=300)
def load_quality() -> pd.DataFrame:
    con = get_connection()
    return con.sql("""
        select q.*, d.latitude, d.longitude
        from prod.mart_station_quality as q
        left join prod.dim_stations as d on q.station_id = d.station_id
    """).df()


@st.cache_data(ttl=300)
def load_freshness() -> pd.DataFrame:
    con = get_connection()
    return con.sql("""
        select
            max(ingested_at) as last_snapshot,
            datediff('minute', max(ingested_at), current_timestamp) as minutes_since_last_snapshot
        from prod.fct_station_availability
    """).df()


quality_df = load_quality()
freshness_df = load_freshness()

with st.sidebar:
    st.header("À propos")
    st.markdown(
        "Ce dashboard consomme les marts dbt du pipeline "
        "[velov-analytics](https://github.com/goldenhubx/velov-analytics) : "
        "ingestion GBFS toutes les 15 min, transformation dbt, tests de qualité "
        "de données. Voir le README pour le détail des cas d'étude."
    )

    st.header("Filtres")
    selected_statuses = st.multiselect(
        "Statut qualité",
        options=list(STATUS_LABELS.keys()),
        default=list(STATUS_LABELS.keys()),
        format_func=lambda s: STATUS_LABELS[s],
    )
    search_name = st.text_input("Rechercher une station")

    st.header("Légende des statuts")
    for status, label in STATUS_LABELS.items():
        color = STATUS_COLORS[status]
        st.markdown(
            f"<span style='color:rgb({color[0]},{color[1]},{color[2]})'>●</span> {label}",
            unsafe_allow_html=True,
        )

st.title("Vélo'v — Qualité & état du réseau")

col1, col2, col3 = st.columns(3)
col1.metric("Stations suivies", len(quality_df))
pct_ok = round(100 * (quality_df["quality_status"] == "ok").mean(), 1)
col2.metric("Part de stations OK", f"{pct_ok} %")
col3.metric(
    "Minutes depuis le dernier snapshot",
    int(freshness_df["minutes_since_last_snapshot"].iloc[0]),
)

filtered_df = quality_df[quality_df["quality_status"].isin(selected_statuses)]
if search_name:
    filtered_df = filtered_df[
        filtered_df["station_name"].str.contains(search_name, case=False, na=False)
    ]

tab_overview, tab_watch = st.tabs(["Vue d'ensemble", "Stations à surveiller"])

with tab_overview:
    st.caption(
        "Chaque station est classée `ok` ou dans l'un des quatre statuts d'anomalie "
        "détaillés dans la légende, à partir de son historique complet."
    )
    st.subheader("Répartition par statut qualité")
    st.dataframe(
        filtered_df["quality_status"]
        .value_counts()
        .rename_axis("quality_status")
        .reset_index(name="n_stations"),
        width="stretch",
    )

with tab_watch:
    watch_df = filtered_df[filtered_df["quality_status"] != "ok"].copy()

    st.caption(
        f"{len(watch_df)} station(s) sur {len(filtered_df)} filtrée(s) présentent une anomalie."
    )

    display_df = watch_df[
        [
            "station_id",
            "station_name",
            "quality_status",
            "hours_since_last_report",
            "share_gap_when_operational",
        ]
    ].sort_values(["quality_status", "station_id"])

    st.dataframe(
        display_df,
        width="stretch",
        column_config={
            "station_id": "ID station",
            "station_name": "Nom",
            "quality_status": st.column_config.TextColumn(
                "Statut", help="Voir légende dans la barre latérale"
            ),
            "hours_since_last_report": st.column_config.NumberColumn(
                "Dernier rapport (h)", format="%.1f"
            ),
            "share_gap_when_operational": st.column_config.NumberColumn(
                "% écart quand opérationnelle", format="%.1f%%"
            ),
        },
    )

    st.subheader("Carte")
    if len(watch_df) > 0:
        watch_df["color"] = watch_df["quality_status"].map(STATUS_COLORS)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=watch_df,
            get_position=["longitude", "latitude"],
            get_fill_color="color",
            get_radius=80,
            pickable=True,
        )
        view_state = pdk.ViewState(
            latitude=watch_df["latitude"].mean(),
            longitude=watch_df["longitude"].mean(),
            zoom=11,
        )
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{station_name}\n{quality_status}"},
            )
        )
    else:
        st.info("Aucune station à afficher avec les filtres actuels.")
