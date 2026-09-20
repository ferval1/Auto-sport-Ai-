import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Lumen Sports AI Auto", page_icon="🏆", layout="wide")
st.title("🏆 Lumen Sports AI — Automático")
st.caption("Las probabilidades son estimaciones experimentales, no garantías.")

LEAGUES = {
    "NBA": "basketball/nba",
    "NFL": "football/nfl",
    "MLB": "baseball/mlb",
    "NHL": "hockey/nhl",
    "Premier League": "soccer/eng.1",
    "La Liga": "soccer/esp.1",
    "Champions League": "soccer/uefa.champions",
    "MLS": "soccer/usa.1",
    "ATP Tennis": "tennis/atp",
    "WTA Tennis": "tennis/wta",
}

def fetch_events(league, day):
    url=f"https://site.api.espn.com/apis/site/v2/sports/{league}/scoreboard"
    r=requests.get(url, params={"dates": day.strftime("%Y%m%d")}, timeout=20)
    r.raise_for_status()
    return r.json().get("events", [])

def get_teams(event):
    competitors=event.get("competitions",[{}])[0].get("competitors",[])
    home=next((x for x in competitors if x.get("homeAway")=="home"), None)
    away=next((x for x in competitors if x.get("homeAway")=="away"), None)
    if not home or not away:
        if len(competitors)>=2:
            home,away=competitors[0],competitors[1]
        else:
            return None,None
    return (home.get("team",{}).get("displayName","Local"),
            away.get("team",{}).get("displayName","Visitante"))

def baseline_probability(event):
    # Conservative baseline until a sport-specific historical model is connected.
    competitors=event.get("competitions",[{}])[0].get("competitors",[])
    home=next((x for x in competitors if x.get("homeAway")=="home"), None)
    away=next((x for x in competitors if x.get("homeAway")=="away"), None)
    if home and away:
        hs=home.get("records",[])
        as_=away.get("records",[])
        # No fabricated advantage from missing data.
        return 0.54,0.46
    return 0.50,0.50

with st.sidebar:
    st.header("Filtros")
    selected_leagues=st.multiselect("Ligas", list(LEAGUES), default=["NBA","NFL","Premier League"])
    start=date.today()
    end=st.date_input("Hasta qué fecha", value=start+timedelta(days=7), min_value=start)
    if end < start:
        st.error("La fecha final debe ser igual o posterior a la inicial.")

if st.button("🔄 Buscar partidos automáticamente", type="primary"):
    all_rows=[]
    current=start
    while current <= end:
        for league_name in selected_leagues:
            try:
                events=fetch_events(LEAGUES[league_name], current)
                for event in events:
                    home,away=get_teams(event)
                    if not home or not away: continue
                    ph,pa=baseline_probability(event)
                    all_rows.append({
                        "Fecha": current.isoformat(),
                        "Liga": league_name,
                        "Local": home,
                        "Visitante": away,
                        "Local %": round(ph*100,1),
                        "Visitante %": round(pa*100,1),
                        "Evento ID": event.get("id","")
                    })
            except Exception as e:
                st.warning(f"No se pudo consultar {league_name} el {current}: {e}")
        current += timedelta(days=1)

    if all_rows:
        df=pd.DataFrame(all_rows)
        st.session_state["games"]=df
    else:
        st.info("No se encontraron partidos con los filtros seleccionados.")

if "games" in st.session_state:
    df=st.session_state["games"]
    st.success(f"{len(df)} partidos encontrados.")
    st.dataframe(df.drop(columns=["Evento ID"]), use_container_width=True, hide_index=True)
    st.download_button("Descargar CSV", df.to_csv(index=False), "lumen_sports_predictions.csv", "text/csv")
    st.warning("Esta versión obtiene calendarios automáticamente, pero sus porcentajes son una línea base. El siguiente paso es conectar estadísticas históricas, lesiones, cuotas y modelos calibrados por deporte. No deben interpretarse como probabilidades validadas.")
else:
    st.info("Elige las ligas y pulsa 'Buscar partidos automáticamente'.")
