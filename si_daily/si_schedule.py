"""Schedule and travel factors for the Sports Insights Daily dashboard.

For every team on today's slate this pulls the team's recent and upcoming games
from ESPN's public scoreboard feed and works out situational factors: rest days,
back-to-backs, games and home/away split over the last 7 and 14 days, miles
travelled, time-zone shifts, road-trip / homestand position, schedule density
(3-in-4, 4-in-6), altitude, streaks, the next game (look-ahead spots) and
overtime minutes / extra innings. For NHL teams it also reads the NHL's own feed
(api-web.nhle.com) for starting-goalie workload and exact OT minutes; goalie
streaks count starts within the last 21 days.

Usage (needs only the Python standard library):
    python si_daily/si_schedule.py --games si_games_20261019.json
    python si_daily/si_schedule.py --matchups "NHL:ANA@NYR,NFL:WSH@SF,MLB:CLE@TB"

Writes si_daily/out/si_schedule_YYYYMMDD.json (one row per team per game).
"""

import argparse
import datetime as dt
import json
import math
import os
import sys
import unicodedata
import urllib.request

LEAGUES = {
    "NFL": "football/nfl",
    "NHL": "hockey/nhl",
    "NBA": "basketball/nba",
    "MLB": "baseball/mlb",
}

# Sports Insights / common abbreviations -> ESPN abbreviations
ALIASES = {
    "NHL": {"SJS": "SJ", "UTA": "UTAH", "LAK": "LA", "NJD": "NJ", "TBL": "TB", "VEG": "VGK",
            "WAS": "WSH", "MON": "MTL", "CLB": "CBJ", "NAS": "NSH", "CAL": "CGY", "WIN": "WPG"},
    "NBA": {"GSW": "GS", "NOP": "NO", "NYK": "NY", "SAS": "SA", "UTA": "UTAH", "PHO": "PHX",
            "BRK": "BKN", "WAS": "WSH"},
    "NFL": {"WAS": "WSH", "JAC": "JAX", "LA": "LAR", "LVR": "LV", "OAK": "LV", "SD": "LAC"},
    "MLB": {"CWS": "CHW", "OAK": "ATH", "KCR": "KC", "SDP": "SD", "SFG": "SF", "TBR": "TB",
            "WSN": "WSH", "WAS": "WSH", "AZ": "ARI", "ARZ": "ARI"},
}

# Home venue per team: (lat, lon, standard UTC offset, observes DST, altitude ft)
E, C, M, P = -5, -6, -7, -8
HOME = {
    "NHL": {
        "ANA": (33.808, -117.877, P, 1, 0), "BOS": (42.366, -71.062, E, 1, 0), "BUF": (42.875, -78.876, E, 1, 0),
        "CGY": (51.037, -114.052, M, 1, 3400), "CAR": (35.803, -78.722, E, 1, 0), "CHI": (41.881, -87.674, C, 1, 0),
        "COL": (39.749, -105.008, M, 1, 5280), "CBJ": (39.969, -83.006, E, 1, 0), "DAL": (32.790, -96.810, C, 1, 0),
        "DET": (42.341, -83.055, E, 1, 0), "EDM": (53.547, -113.498, M, 1, 2200), "FLA": (26.158, -80.326, E, 1, 0),
        "LA": (34.043, -118.267, P, 1, 0), "MIN": (44.945, -93.101, C, 1, 0), "MTL": (45.496, -73.569, E, 1, 0),
        "NSH": (36.159, -86.779, C, 1, 0), "NJ": (40.734, -74.171, E, 1, 0), "NYI": (40.712, -73.726, E, 1, 0),
        "NYR": (40.750, -73.993, E, 1, 0), "OTT": (45.297, -75.927, E, 1, 0), "PHI": (39.901, -75.172, E, 1, 0),
        "PIT": (40.439, -79.989, E, 1, 0), "SJ": (37.333, -121.901, P, 1, 0), "SEA": (47.622, -122.354, P, 1, 0),
        "STL": (38.627, -90.203, C, 1, 0), "TB": (27.943, -82.452, E, 1, 0), "TOR": (43.643, -79.379, E, 1, 0),
        "UTAH": (40.768, -111.901, M, 1, 4300), "VAN": (49.278, -123.109, P, 1, 0), "VGK": (36.103, -115.178, P, 1, 2000),
        "WSH": (38.898, -77.021, E, 1, 0), "WPG": (49.893, -97.144, C, 1, 0),
    },
    "NBA": {
        "ATL": (33.757, -84.396, E, 1, 1000), "BOS": (42.366, -71.062, E, 1, 0), "BKN": (40.683, -73.976, E, 1, 0),
        "CHA": (35.225, -80.839, E, 1, 0), "CHI": (41.881, -87.674, C, 1, 0), "CLE": (41.497, -81.688, E, 1, 0),
        "DAL": (32.790, -96.810, C, 1, 0), "DEN": (39.749, -105.008, M, 1, 5280), "DET": (42.341, -83.055, E, 1, 0),
        "GS": (37.768, -122.388, P, 1, 0), "HOU": (29.751, -95.362, C, 1, 0), "IND": (39.764, -86.155, E, 1, 0),
        "LAC": (33.945, -118.343, P, 1, 0), "LAL": (34.043, -118.267, P, 1, 0), "MEM": (35.138, -90.051, C, 1, 0),
        "MIA": (25.781, -80.188, E, 1, 0), "MIL": (43.045, -87.918, C, 1, 0), "MIN": (44.979, -93.276, C, 1, 0),
        "NO": (29.949, -90.082, C, 1, 0), "NY": (40.750, -73.993, E, 1, 0), "OKC": (35.463, -97.515, C, 1, 1200),
        "ORL": (28.539, -81.384, E, 1, 0), "PHI": (39.901, -75.172, E, 1, 0), "PHX": (33.446, -112.071, M, 0, 1100),
        "POR": (45.532, -122.667, P, 1, 0), "SAC": (38.580, -121.500, P, 1, 0), "SA": (29.427, -98.437, C, 1, 0),
        "TOR": (43.643, -79.379, E, 1, 0), "UTAH": (40.768, -111.901, M, 1, 4300), "WSH": (38.898, -77.021, E, 1, 0),
    },
    "NFL": {
        "ARI": (33.528, -112.263, M, 0, 1100), "ATL": (33.755, -84.401, E, 1, 1000), "BAL": (39.278, -76.623, E, 1, 0),
        "BUF": (42.774, -78.787, E, 1, 0), "CAR": (35.226, -80.853, E, 1, 0), "CHI": (41.862, -87.617, C, 1, 0),
        "CIN": (39.095, -84.516, E, 1, 0), "CLE": (41.506, -81.700, E, 1, 0), "DAL": (32.748, -97.093, C, 1, 0),
        "DEN": (39.744, -105.020, M, 1, 5280), "DET": (42.340, -83.046, E, 1, 0), "GB": (44.501, -88.062, C, 1, 0),
        "HOU": (29.685, -95.411, C, 1, 0), "IND": (39.760, -86.164, E, 1, 0), "JAX": (30.324, -81.637, E, 1, 0),
        "KC": (39.049, -94.484, C, 1, 0), "LV": (36.091, -115.184, P, 1, 2000), "LAC": (33.953, -118.339, P, 1, 0),
        "LAR": (33.953, -118.339, P, 1, 0), "MIA": (25.958, -80.239, E, 1, 0), "MIN": (44.974, -93.258, C, 1, 0),
        "NE": (42.091, -71.264, E, 1, 0), "NO": (29.951, -90.081, C, 1, 0), "NYG": (40.814, -74.074, E, 1, 0),
        "NYJ": (40.814, -74.074, E, 1, 0), "PHI": (39.901, -75.168, E, 1, 0), "PIT": (40.447, -80.016, E, 1, 0),
        "SF": (37.403, -121.970, P, 1, 0), "SEA": (47.595, -122.332, P, 1, 0), "TB": (27.976, -82.503, E, 1, 0),
        "TEN": (36.166, -86.771, C, 1, 0), "WSH": (38.908, -76.864, E, 1, 0),
    },
    "MLB": {
        "ARI": (33.445, -112.067, M, 0, 1100), "ATH": (38.580, -121.514, P, 1, 0), "ATL": (33.891, -84.468, E, 1, 1000),
        "BAL": (39.284, -76.622, E, 1, 0), "BOS": (42.346, -71.097, E, 1, 0), "CHC": (41.948, -87.656, C, 1, 0),
        "CHW": (41.830, -87.634, C, 1, 0), "CIN": (39.097, -84.507, E, 1, 0), "CLE": (41.496, -81.685, E, 1, 0),
        "COL": (39.756, -104.994, M, 1, 5200), "DET": (42.339, -83.049, E, 1, 0), "HOU": (29.757, -95.355, C, 1, 0),
        "KC": (39.051, -94.480, C, 1, 0), "LAA": (33.800, -117.883, P, 1, 0), "LAD": (34.074, -118.240, P, 1, 0),
        "MIA": (25.778, -80.220, E, 1, 0), "MIL": (43.028, -87.971, C, 1, 0), "MIN": (44.982, -93.278, C, 1, 0),
        "NYM": (40.757, -73.846, E, 1, 0), "NYY": (40.829, -73.926, E, 1, 0), "PHI": (39.906, -75.166, E, 1, 0),
        "PIT": (40.447, -80.006, E, 1, 0), "SD": (32.707, -117.157, P, 1, 0), "SF": (37.778, -122.389, P, 1, 0),
        "SEA": (47.591, -122.332, P, 1, 0), "STL": (38.623, -90.193, C, 1, 0), "TB": (27.768, -82.653, E, 1, 0),
        "TEX": (32.747, -97.084, C, 1, 0), "TOR": (43.641, -79.389, E, 1, 0), "WSH": (38.873, -77.007, E, 1, 0),
    },
}

# Neutral-site cities seen in international / special games: (lat, lon, UTC offset, DST, altitude)
NEUTRAL = {
    "London": (51.556, -0.280, 0, 0, 0), "Mexico City": (19.303, -99.150, -6, 0, 7350),
    "Munich": (48.219, 11.625, 1, 0, 1700), "Berlin": (52.515, 13.239, 1, 0, 0),
    "Frankfurt": (50.069, 8.645, 1, 0, 0), "Madrid": (40.453, -3.688, 1, 0, 2100),
    "Dublin": (53.335, -6.228, 0, 0, 0), "Sao Paulo": (-23.545, -46.474, -3, 0, 2600),
    "São Paulo": (-23.545, -46.474, -3, 0, 2600), "Paris": (48.841, 2.253, 1, 0, 0),
    "Stockholm": (59.372, 18.004, 1, 0, 0), "Helsinki": (60.205, 24.928, 2, 0, 0),
    "Prague": (50.106, 14.493, 1, 0, 0), "Tampere": (61.494, 23.776, 2, 0, 0),
    "Tokyo": (35.706, 139.752, 9, 0, 0), "Seoul": (37.512, 127.072, 9, 0, 0),
    "Melbourne": (-37.820, 144.983, 10, 0, 0), "Abu Dhabi": (24.467, 54.603, 4, 0, 0),
    "San Juan": (18.418, -66.071, -4, 0, 0), "Honolulu": (21.373, -157.930, -10, 0, 0),
}

TZ_NAME = {-5: "ET", -6: "CT", -7: "MT", -8: "PT"}
SPANS = (7, 14)
COLUMNS = ["rest_days", "b2b", *[f"{k}{n}" for n in SPANS for k in ("g", "home", "away", "mi")], "mi_in",
           "tz_shift", "start_local", "body_clock", "trip", "density", "streak", "last5", "prev", "next",
           "altitude", "ot7", "ot14", "ot_min7", "ot_min14", "extra14",
           "goalie", "goalie_src", "goalie_last", "goalie_starts7", "goalie_starts14", "goalie_streak", "goalie_sa7", "goalie_b2b", "goalies",
           "flags", "note"]

# ESPN -> NHL API team codes where they differ
NHL_CODE = {"SJ": "SJS", "UTAH": "UTA", "LA": "LAK", "NJ": "NJD", "TB": "TBL"}


def miles(a, b):
    if a is None or b is None:
        return None
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def us_dst(utc):
    """True when US/Canada daylight time is in effect at this UTC instant (2nd Sun Mar - 1st Sun Nov, ~2am ET)."""
    y = utc.year
    mar = dt.datetime(y, 3, 8 + (6 - dt.date(y, 3, 8).weekday()) % 7, 7)
    nov = dt.datetime(y, 11, 1 + (6 - dt.date(y, 11, 1).weekday()) % 7, 6)
    return mar <= utc.replace(tzinfo=None) < nov


def offset(loc, utc):
    return loc[2] + (1 if loc[3] and us_dst(utc) else 0)


def local(loc, utc):
    return utc + dt.timedelta(hours=offset(loc, utc))


def fetch(league, start, end):
    return get_json(f"https://site.api.espn.com/apis/site/v2/sports/{LEAGUES[league]}/scoreboard"
                    f"?dates={start:%Y%m%d}-{end:%Y%m%d}&limit=1000").get("events", [])


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def mmss(t):
    m, s = (t or "0:00").split(":")
    return int(m) + int(s) / 60


def extra_time(detail, league):
    """ESPN final detail ("Final/OT", "Final/2OT", "Final/SO", "Final/11") -> (past regulation?, OT minutes, extra innings)."""
    if "/" not in (detail or ""):
        return False, 0, 0
    suf = detail.split("/")[-1].strip().upper()
    n = int(suf[:-2]) if suf.endswith("OT") and suf[:-2].isdigit() else 1
    if league == "MLB":
        return True, None, max(0, int(suf) - 9) if suf.isdigit() else None
    if league == "NBA":
        return True, 5 * n, 0
    if league == "NHL" and suf == "SO":
        return True, 5, 0
    return True, None, 0  # NHL OT length comes from the NHL feed; NFL OT length isn't in ESPN's summary


def nhl_workload(code, today):
    """From the NHL's own feed: starting-goalie workload and exact OT minutes for the last 21 days.

    Returns {"ot": {date: minutes}, "starts": [(date, goalie, minutes, shots against)], newest last}.
    """
    season = f"{today.year}{today.year + 1}" if today.month >= 9 else f"{today.year - 1}{today.year}"
    base = "https://api-web.nhle.com/v1"
    sched = get_json(f"{base}/club-schedule-season/{code}/{season}").get("games", [])
    out = {"ot": {}, "starts": []}
    for g in sched:
        day = dt.date.fromisoformat(g["gameDate"])
        if not (today - dt.timedelta(days=21) <= day < today) or g.get("gameState") not in ("OFF", "FINAL"):
            continue
        box = get_json(f"{base}/gamecenter/{g['id']}/boxscore")
        side = "homeTeam" if box["homeTeam"]["abbrev"] == code else "awayTeam"
        goalies = [x for x in box.get("playerByGameStats", {}).get(side, {}).get("goalies", []) if mmss(x.get("toi")) > 0]
        start = next((x for x in goalies if x.get("starter")), goalies[0] if goalies else None)
        if start:
            out["starts"].append((day, start["name"]["default"], mmss(start.get("toi")), start.get("shotsAgainst") or 0))
        last = (g.get("gameOutcome") or {}).get("lastPeriodType")
        if last in ("OT", "SO"):
            per = 20 if g.get("gameType") == 3 else 5
            if last == "SO":
                out["ot"][day] = per
            else:
                land = get_json(f"{base}/gamecenter/{g['id']}/landing")
                goals = [(p["periodDescriptor"]["number"], gl.get("timeInPeriod"))
                         for p in land.get("summary", {}).get("scoring", []) for gl in p.get("goals", [])]
                num, t = max(goals, key=lambda x: (x[0], mmss(x[1]))) if goals else (4, f"{per}:00")
                out["ot"][day] = round((num - 4) * per + mmss(t), 1)
    out["starts"].sort(key=lambda x: x[0])
    return out


GOALIE_COLS = ["goalie", "goalie_src", "goalie_last", "goalie_starts7", "goalie_starts14", "goalie_streak",
               "goalie_sa7", "goalie_b2b", "goalies"]


def name_key(name):
    """'Lukas Dostal', 'L. Dostal' and 'Dostal' all match: last name plus first initial when both sides have one."""
    parts = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower().replace(".", " ").split()
    return (parts[-1], parts[0][0] if len(parts) > 1 else "") if parts else ("", "")


def same_goalie(a, b):
    (la, ia), (lb, ib) = name_key(a), name_key(b)
    return la == lb and (not ia or not ib or ia == ib)


def goalie_fields(w, today, listed=None):
    """Workload of the goalie Sports Insights lists for today (`listed` = (name, status)); else of the last starter."""
    starts = w["starts"]
    r = dict.fromkeys(GOALIE_COLS, "")
    in_days = lambda n, name=None: [s for s in starts if (today - s[0]).days <= n and (name is None or same_goalie(s[1], name))]
    r["goalie_last"] = starts[-1][1] if starts else ""
    if listed and listed[0]:
        who, r["goalie_src"] = listed[0], "Sports Insights" + (f" ({listed[1]})" if listed[1] else "")
    elif starts:
        who, r["goalie_src"] = starts[-1][1], "Last starter (Sports Insights listed none)"
    else:
        return r
    k = 0
    for s in reversed(starts):
        if not same_goalie(s[1], who):
            break
        k += 1
    mine = in_days(21, who)
    r.update(goalie=who, goalie_starts7=len(in_days(7, who)), goalie_starts14=len(in_days(14, who)),
             goalie_streak=k, goalie_sa7=sum(s[3] for s in in_days(7, who)),
             goalie_b2b="Yes" if mine and (today - mine[-1][0]).days == 1 else "No")
    parts = []
    for name in sorted({s[1] for s in in_days(14)}, key=lambda n: -len(in_days(14, n))):
        g14 = in_days(14, name)
        parts.append(f"{name}: {len(in_days(7, name))} start{plural(in_days(7, name))} 7d / {len(g14)} in 14d, "
                     f"{sum(s[3] for s in g14)} shots, {round(sum(s[2] for s in g14))} min in 14d")
    if not mine:
        parts.insert(0, f"{who}: no starts in the last 21 days")
    r["goalies"] = "; ".join(parts)
    return r


def parse(events, league):
    """ESPN events -> list of game dicts with a resolved location."""
    games = []
    for ev in events:
        comp = (ev.get("competitions") or [{}])[0]
        teams = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        if "home" not in teams or "away" not in teams:
            continue
        home, away = teams["home"]["team"]["abbreviation"], teams["away"]["team"]["abbreviation"]
        loc, label = HOME[league].get(home), home
        if comp.get("neutralSite"):
            city = ((comp.get("venue") or {}).get("address") or {}).get("city", "")
            loc, label = NEUTRAL.get(city, loc), city or "neutral site"
        status = ((comp.get("status") or ev.get("status") or {}).get("type") or {})
        games.append({
            "utc": dt.datetime.strptime(ev["date"][:16], "%Y-%m-%dT%H:%M").replace(tzinfo=dt.timezone.utc),
            "home": home, "away": away, "loc": loc, "where": label,
            "neutral": bool(comp.get("neutralSite")),
            "done": bool(status.get("completed")), "detail": status.get("shortDetail", ""),
            "score": {k: teams[k].get("score") for k in ("home", "away")},
            "winner": next((teams[k]["team"]["abbreviation"] for k in teams if teams[k].get("winner")), None),
        })
    games.sort(key=lambda g: g["utc"])
    return games


def team_games(games, team):
    out = []
    for g in games:
        if team in (g["home"], g["away"]):
            side = "home" if g["home"] == team else "away"
            out.append(dict(g, side=side, opp=g["away"] if side == "home" else g["home"],
                            day=local(g["loc"], g["utc"]).date() if g["loc"] else g["utc"].date()))
    return out


def plural(n):
    return "" if (n if isinstance(n, int) else len(n)) == 1 else "s"


def fmt_day(d):
    return f"{d:%b} {d.day}"


def factors(league, team, opp, today, games, goalie=None):
    """All situational factors for `team` in its game against `opp` on `today`."""
    tg = team_games(games, team)
    idx = next((i for i, g in enumerate(tg) if g["opp"] == opp and abs((g["day"] - today).days) <= 1), None)
    if idx is None:
        return dict.fromkeys(COLUMNS, "") | {"note": f"{team} vs {opp} not found in ESPN schedule"}
    cur, prev, nxt = tg[idx], tg[:idx], tg[idx + 1:]
    home_loc = HOME[league].get(team)
    nfl = league == "NFL"
    r = {}

    # Rest
    last = prev[-1] if prev else None
    r["rest_days"] = (cur["day"] - last["day"]).days - 1 if last else None
    r["b2b"] = "Yes" if r["rest_days"] == 0 else "No"

    # Where the team is coming from: NFL teams fly home between games, others hop city to city
    def origin(i):
        if nfl or i == 0:
            return home_loc
        return tg[i - 1]["loc"]

    def leg(i):
        g = tg[i]
        d = miles(origin(i), g["loc"]) or 0
        if nfl and g["side"] == "away":
            d *= 2 if i != idx else 1  # past NFL road games are round trips
        return d

    r["mi_in"] = round(leg(idx))
    for n in SPANS:
        lo = today - dt.timedelta(days=n)
        window = [g for g in prev if lo <= g["day"] < today]
        r[f"g{n}"] = len(window)
        r[f"home{n}"] = sum(g["side"] == "home" for g in window)
        r[f"away{n}"] = sum(g["side"] == "away" for g in window)
        r[f"mi{n}"] = round(sum(leg(i) for i, g in enumerate(tg) if lo <= g["day"] <= today and i <= idx))

    # Time zones: shift since the last game, and today's start on the team's home clock
    if cur["loc"] and home_loc:
        cur_off = offset(cur["loc"], cur["utc"])
        prev_loc = origin(idx)
        r["tz_shift"] = cur_off - offset(prev_loc, cur["utc"]) if prev_loc else 0
        body = cur["utc"] + dt.timedelta(hours=offset(home_loc, cur["utc"]))
        loc_start = local(cur["loc"], cur["utc"])
        r["start_local"] = loc_start.strftime("%I:%M %p").lstrip("0")
        r["body_clock"] = body.strftime("%I:%M %p").lstrip("0") + " " + TZ_NAME.get(home_loc[2], "home")
    else:
        r["tz_shift"], r["start_local"], r["body_clock"] = None, "", ""

    # Road trip / homestand position and length
    def run(seq):
        k = 0
        for g in seq:
            if g["side"] != cur["side"]:
                break
            k += 1
        return k
    back, ahead = run(reversed(tg[:idx + 1])), run(nxt)
    kind = "road trip" if cur["side"] == "away" else "homestand"
    r["trip"] = f"Game {back} of {back + ahead} on {kind}" + ("+" if not nxt or ahead == len(nxt) else "")

    # Density (hockey / basketball)
    in_n = lambda n: sum(1 for g in tg[:idx + 1] if (today - g["day"]).days < n)
    dense = []
    if league in ("NHL", "NBA"):
        if in_n(4) >= 3:
            dense.append(f"{in_n(4)} in 4 nights")
        if in_n(6) >= 4:
            dense.append(f"{in_n(6)} in 6 nights")
    r["density"] = ", ".join(dense)

    # Form
    done = [g for g in prev if g["done"]]
    res = ["W" if g["winner"] == team else "L" for g in done if g["winner"]]
    streak = ""
    if res:
        k = 1
        while k < len(res) and res[-k - 1] == res[-1]:
            k += 1
        streak = f"{res[-1]}{k}"
    r["streak"] = streak

    # Overtime / extra innings in the last 7 and 14 days
    nhl = r_nhl = None
    if league == "NHL":
        try:
            nhl = nhl_workload(NHL_CODE.get(team, team), today)
        except Exception as e:  # keep the rest of the row if the NHL feed is down
            r_nhl = f"NHL feed unavailable ({e.__class__.__name__}); goalie and OT minutes missing"
    for n in SPANS:
        window = [g for g in prev if g["done"] and (today - g["day"]).days <= n]
        ex = [(g, *extra_time(g["detail"], league)) for g in window]
        ex = [e for e in ex if e[1]]
        r[f"ot{n}"] = len(ex)
        if league in ("NHL", "NBA"):
            mins = [(nhl["ot"].get(g["day"]) if nhl and nhl["ot"].get(g["day"]) is not None else m) for g, _, m, _ in ex]
            r[f"ot_min{n}"] = round(sum(m for m in mins if m is not None), 1) if all(m is not None for m in mins) else ""
        else:
            r[f"ot_min{n}"] = ""
        if n == 14:
            if league == "MLB":
                inn = sum(i or 0 for *_, i in ex)
                r["extra14"] = f"{len(ex)} extra-inning game{plural(ex)}, {inn} extra inning{plural(inn)}" if ex else "None"
            elif league == "NFL":
                r["extra14"] = f"{len(ex)} OT game{plural(ex)}" if ex else "None"
            else:
                r["extra14"] = (f"{len(ex)} OT game{plural(ex)}" + (f", {r['ot_min14']} OT min" if r["ot_min14"] != "" else "")) if ex else "None"
    r.update(goalie_fields(nhl, today, goalie) if nhl else dict.fromkeys(GOALIE_COLS, ""))
    if league == "NHL" and nhl is None and goalie and goalie[0]:
        r.update(goalie=goalie[0], goalie_src="Sports Insights" + (f" ({goalie[1]})" if goalie[1] else ""))
    r["last5"] = f"{res[-5:].count('W')}-{res[-5:].count('L')}" if res else ""
    if last:
        sc = last["score"]
        us, them = sc[last["side"]], sc["away" if last["side"] == "home" else "home"]
        wl = ("W" if last["winner"] == team else "L") if last["winner"] else ""
        extra = f" ({last['detail'].split('/')[-1]})" if "/" in (last.get("detail") or "") else ""
        at = "vs" if last["side"] == "home" else "@"
        r["prev"] = f"{fmt_day(last['day'])} {at} {last['opp']}: {wl} {us}-{them}{extra}".strip()
    else:
        r["prev"] = ""
    if nxt:
        n0 = nxt[0]
        r["next"] = f"{fmt_day(n0['day'])} {'vs' if n0['side'] == 'home' else '@'} {n0['opp']} ({(n0['day'] - cur['day']).days - 1}d rest)"
    else:
        r["next"] = ""

    # Altitude
    alt_now = (cur["loc"] or (0, 0, 0, 0, 0))[4]
    r["altitude"] = f"Visiting {alt_now:,} ft" if alt_now >= 4000 and (home_loc or (0,) * 5)[4] < 4000 else ""

    # Plain-language flags
    flags = []
    if r["b2b"] == "Yes":
        flags.append("Back-to-back")
    if r["density"]:
        flags.append(r["density"])
    if nfl and r["rest_days"] is not None:
        if r["rest_days"] <= 4:
            flags.append("Short week")
        elif r["rest_days"] >= 12:
            flags.append("Off bye")
        elif r["rest_days"] >= 9:
            flags.append("Extra rest")
    if cur["side"] == "away" and back >= 3:
        flags.append(f"Road game {back} in a row")
    if r["mi_in"] >= 1500:
        flags.append(f"{r['mi_in']:,} mi trip in")
    if r.get("tz_shift") and abs(r["tz_shift"]) >= 2:
        flags.append(f"{abs(r['tz_shift'])} time zones {'east' if r['tz_shift'] > 0 else 'west'}")
    if league == "MLB" and last and r["rest_days"] == 0 and last["loc"] and cur["loc"]:
        if local(last["loc"], last["utc"]).hour >= 18 and local(cur["loc"], cur["utc"]).hour < 17:
            flags.append("Day game after night game")
    if r["altitude"]:
        flags.append(r["altitude"])
    if last and "/" in (last.get("detail") or ""):
        flags.append("Went to extras last game")
    if nxt and r["next"] and (nxt[0]["day"] - cur["day"]).days <= 1 and league in ("NHL", "NBA"):
        flags.append("Back-to-back tomorrow")
    if cur["neutral"]:
        flags.append(f"Neutral site ({cur['where']})")
    if r["ot_min7"] not in ("", 0) and r["ot_min7"] >= 10:
        flags.append(f"{r['ot_min7']} OT min in last 7 days")
    if r["goalie_b2b"] == "Yes":
        flags.append(f"Goalie {r['goalie']} started last night")
    if r["goalie_streak"] != "" and r["goalie_streak"] >= 5:
        flags.append(f"Goalie {r['goalie']} {r['goalie_streak']} straight starts")
    if r["goalie"] and r["goalie_last"] and r["goalie_src"].startswith("Sports") and not same_goalie(r["goalie"], r["goalie_last"]):
        flags.append(f"Goalie change: {r['goalie']} in for {r['goalie_last']}")
    r["flags"] = "; ".join(flags)
    r["note"] = "; ".join(x for x in ("" if cur["loc"] else "Venue location unknown; travel not counted", r_nhl or "") if x)
    return r


def load_matchups(args):
    """[(sport, game, {team: (goalie, status)})]. Goalies come from the games file's away_goalie / home_goalie
    (+ away_goalie_status / home_goalie_status) or from --goalies "ANA=Lukas Dostal:Confirmed,NYR=Igor Shesterkin"."""
    cli = {}
    for item in filter(None, (args.goalies or "").split(",")):
        team, rest = item.split("=", 1)
        name, _, status = rest.partition(":")
        cli[team.strip()] = (name.strip(), status.strip())
    if args.matchups:
        rows = []
        for m in args.matchups.split(","):
            sport, game = m.strip().split(":")
            rows.append({"sport": sport, "game": game.strip()})
    else:
        with open(args.games, encoding="utf-8") as f:
            rows = json.load(f)
        if isinstance(rows, dict):
            rows = rows.get("rows") or rows.get("data") or rows.get("results") or []
    out = []
    for r in rows:
        away, home = r["game"].split("@")
        g = {away: (r.get("away_goalie"), r.get("away_goalie_status")), home: (r.get("home_goalie"), r.get("home_goalie_status"))}
        g.update({t: v for t, v in cli.items() if t in g})
        out.append((r["sport"].upper(), r["game"], g))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--games", help="today's games JSON (rows with sport and game like ANA@NYR)")
    ap.add_argument("--matchups", help='e.g. "NHL:ANA@NYR,NFL:WSH@SF"')
    ap.add_argument("--goalies", help='Sports Insights listed goalies, e.g. "ANA=Lukas Dostal:Confirmed,NYR=Igor Shesterkin:Expected"')
    ap.add_argument("--date", help="slate date YYYY-MM-DD (default today)")
    ap.add_argument("--out", help="output path (default si_daily/out/si_schedule_YYYYMMDD.json)")
    args = ap.parse_args()
    if not (args.games or args.matchups):
        ap.error("give --games or --matchups")
    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()

    rows, cache = [], {}
    for sport, game, goalies in load_matchups(args):
        if sport not in LEAGUES:
            print(f"skip {sport} {game}: league not supported yet", file=sys.stderr)
            continue
        if sport not in cache:
            cache[sport] = parse(fetch(sport, today - dt.timedelta(days=21), today + dt.timedelta(days=10)), sport)
        away_si, home_si = game.split("@")
        alias = ALIASES.get(sport, {})
        away, home = alias.get(away_si, away_si), alias.get(home_si, home_si)
        for team_si, team, opp, side in ((away_si, away, home, "away"), (home_si, home, away, "home")):
            f = factors(sport, team, opp, today, cache[sport], goalies.get(team_si))
            rows.append(dict({"id": f"{game}|{team_si}", "game": game, "sport": sport,
                              "team": team_si, "side": side}, **f))
            print(f"{game:10} {team_si:5} {f.get('flags') or f.get('note') or '-'}")

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", f"si_schedule_{today:%Y%m%d}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1, default=str)
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
