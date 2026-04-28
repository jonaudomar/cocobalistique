"""
⚡ Production électrique France — Dashboard Streamlit
Source : ODRÉ / éCO2mix (RTE) — données temps réel toutes les 15 min
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Production Électrique France",
    page_icon="⚡",
    layout="wide",
)

ODRE_BASE_URL = (
    "https://odre.opendatasoft.com/api/explore/v2.1"
    "/catalog/datasets/eco2mix-national-tr/records"
)

COLORS = {
    "nucleaire": "#F59E0B",
    "solaire":   "#FCD34D",
    "consommation": "#94A3B8",
}

# ─────────────────────────────────────────────
# RÉCUPÉRATION DES DONNÉES (avec cache 15 min)
# ─────────────────────────────────────────────

@st.cache_data(ttl=900)  # cache 15 minutes = fréquence de l'API
def fetch_production(hours: int = 24) -> pd.DataFrame:
    from datetime import timezone
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    # L'API ODRÉ requiert le préfixe date'' pour les filtres datetime
    url = (
        f"{ODRE_BASE_URL}"
        f"?select=date_heure,nucleaire,solaire,consommation"
        f"&where=date_heure>=date'{start_str}'"
        f"&order_by=date_heure%20asc"
        f"&limit=300"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    records = resp.json().get("results", [])
    if not records:
        raise ValueError("Aucune donnée reçue.")
    df = pd.DataFrame(records)
    df["date_heure"] = pd.to_datetime(df["date_heure"], utc=True).dt.tz_convert("Europe/Paris")
    for col in ["nucleaire", "solaire", "consommation"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["nucleaire", "solaire"]).sort_values("date_heure").reset_index(drop=True)


# ─────────────────────────────────────────────
# EN-TÊTE
# ─────────────────────────────────────────────

st.title("⚡ Production électrique — France")
st.caption("Source : [ODRÉ / éCO2mix (RTE)](https://odre.opendatasoft.com) · Mise à jour toutes les 15 min")

# ─────────────────────────────────────────────
# SIDEBAR — FILTRES
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("Paramètres")
    hours = st.selectbox(
        "Fenêtre temporelle",
        options=[6, 12, 24, 48],
        index=2,
        format_func=lambda h: f"Dernières {h}h",
    )
    show_conso = st.toggle("Afficher la consommation", value=True)
    st.divider()
    if st.button("🔄 Forcer l'actualisation"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Dernière actualisation : {datetime.now().strftime('%H:%M:%S')}")

# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────

with st.spinner("Chargement des données éCO2mix..."):
    try:
        df = fetch_production(hours=hours)
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        st.stop()

last = df.iloc[-1]
total_mix = last["nucleaire"] + last["solaire"]

# ─────────────────────────────────────────────
# MÉTRIQUES
# ─────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "☢️ Nucléaire",
        f"{int(last['nucleaire']):,} MW",
        delta=f"{round(last['nucleaire'] / total_mix * 100, 1)}% du mix",
    )
with col2:
    st.metric(
        "☀️ Solaire",
        f"{int(last['solaire']):,} MW",
        delta=f"{round(last['solaire'] / total_mix * 100, 1)}% du mix",
    )
with col3:
    st.metric(
        "📈 Pic solaire (période)",
        f"{int(df['solaire'].max()):,} MW",
        delta=f"à {df.loc[df['solaire'].idxmax(), 'date_heure'].strftime('%H:%M')}",
    )
with col4:
    avg_nuc = int(df["nucleaire"].mean())
    st.metric(
        "📊 Moy. nucléaire",
        f"{avg_nuc:,} MW",
        delta=f"sur {hours}h",
    )

st.divider()

# ─────────────────────────────────────────────
# GRAPHIQUE PRINCIPAL — Plotly interactif
# ─────────────────────────────────────────────

fig = make_subplots(
    rows=2, cols=1,
    row_heights=[0.72, 0.28],
    shared_xaxes=True,
    vertical_spacing=0.06,
    subplot_titles=("Production par filière (MW)", "Part solaire (%)"),
)

# Courbe nucléaire
fig.add_trace(go.Scatter(
    x=df["date_heure"], y=df["nucleaire"],
    name="Nucléaire",
    line=dict(color=COLORS["nucleaire"], width=2.5),
    fill="tozeroy", fillcolor="rgba(245,158,11,0.1)",
    hovertemplate="<b>Nucléaire</b><br>%{x|%H:%M}<br>%{y:,.0f} MW<extra></extra>",
), row=1, col=1)

# Courbe solaire
fig.add_trace(go.Scatter(
    x=df["date_heure"], y=df["solaire"],
    name="Solaire",
    line=dict(color=COLORS["solaire"], width=2.5, dash="dot"),
    fill="tozeroy", fillcolor="rgba(252,211,77,0.15)",
    hovertemplate="<b>Solaire</b><br>%{x|%H:%M}<br>%{y:,.0f} MW<extra></extra>",
), row=1, col=1)

# Courbe consommation (optionnelle)
if show_conso and "consommation" in df.columns:
    fig.add_trace(go.Scatter(
        x=df["date_heure"], y=df["consommation"],
        name="Consommation",
        line=dict(color=COLORS["consommation"], width=1.5, dash="dash"),
        hovertemplate="<b>Consommation</b><br>%{x|%H:%M}<br>%{y:,.0f} MW<extra></extra>",
    ), row=1, col=1)

# Part solaire (%)
part_solaire = df["solaire"] / (df["nucleaire"] + df["solaire"]) * 100
fig.add_trace(go.Scatter(
    x=df["date_heure"], y=part_solaire.round(2),
    name="Part solaire (%)",
    line=dict(color=COLORS["solaire"], width=2),
    fill="tozeroy", fillcolor="rgba(252,211,77,0.2)",
    showlegend=False,
    hovertemplate="<b>Part solaire</b><br>%{x|%H:%M}<br>%{y:.1f}%<extra></extra>",
), row=2, col=1)

fig.update_layout(
    height=520,
    hovermode="x unified",
    legend=dict(orientation="h", y=1.04, x=0),
    margin=dict(l=0, r=0, t=40, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis2=dict(tickformat="%H:%M"),
)
fig.update_yaxes(gridcolor="rgba(100,100,100,0.15)", tickformat=",.0f", row=1, col=1)
fig.update_yaxes(gridcolor="rgba(100,100,100,0.15)", ticksuffix="%", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# TABLEAU DE DONNÉES BRUTES (optionnel)
# ─────────────────────────────────────────────

with st.expander("📋 Voir les données brutes"):
    display_df = df[["date_heure", "nucleaire", "solaire", "consommation"]].copy()
    display_df["date_heure"] = display_df["date_heure"].dt.strftime("%d/%m %H:%M")
    display_df.columns = ["Date/Heure", "Nucléaire (MW)", "Solaire (MW)", "Consommation (MW)"]
    st.dataframe(display_df.iloc[::-1], use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Télécharger CSV",
        data=csv,
        file_name=f"production_electrique_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────
# RAFRAÎCHISSEMENT AUTOMATIQUE
# ─────────────────────────────────────────────

st.divider()
auto_refresh = st.toggle("Rafraîchissement automatique (15 min)", value=False)
if auto_refresh:
    import time
    st.info("⏳ La page se rafraîchira automatiquement toutes les 15 minutes.")
    time.sleep(900)
    st.cache_data.clear()
    st.rerun()
