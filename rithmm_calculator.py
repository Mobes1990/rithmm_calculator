import streamlit as st
import pandas as pd
import numpy as np
import re
import os

# ============================================================
# CONFIGURATION & FILE PATHS
# ============================================================
# Verify that these files exist exactly at these locations.
PATH_ROZIER = r"C:\Users\sarah\OneDrive\Rithmm - Adam\Python\Scripts\32529 rozier copy.xlsx"     
PATH_BIG_MONEY = r"C:\Users\sarah\OneDrive\Rithmm - Adam\Python\Scripts\32925 big money copy.xlsx"  
PATH_HEBRON = r"C:\Users\sarah\OneDrive\Rithmm - Adam\Python\Scripts\32925 Hebron lames copy.xlsx"   

# ============================================================
# FUNCTION: LOAD RAW DATA
# ============================================================
def load_raw_data():
    # Check if files exist
    file_paths = [PATH_ROZIER, PATH_BIG_MONEY, PATH_HEBRON]
    missing_files = [path for path in file_paths if not os.path.exists(path)]
    if missing_files:
        st.error("The following file(s) were not found:\n" + "\n".join(missing_files))
        st.stop()
    
    files = {
        "Terry Rozier": PATH_ROZIER,
        "BigMoney": PATH_BIG_MONEY,
        "Jebron Lames": PATH_HEBRON
    }
    
    frames = []
    for model, path in files.items():
        try:
            df = pd.read_excel(path, sheet_name="in")
        except Exception as e:
            st.error(f"Error loading file for {model} from {path}:\n{e}")
            continue
        # Force the model name to be exactly the model string
        df["model name"] = model
        frames.append(df)
    
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        return combined
    else:
        st.error("No raw data could be loaded.")
        st.stop()

# ============================================================
# FUNCTION: PREPROCESS DATA
# ============================================================
def preprocess_data(df):
    """
    Preprocess the data:
      - If "bet type" is missing, use "spread_type" if available; else default to "Favorite Spreads".
      - Create "home/away" column if missing:
            * If "bet" column exists, infer "Home" if "HOME" is in the text,
              "Away" if "AWAY" is in the text, else "Both".
            * Otherwise, if "home team" exists, default to "Home"; else "Both".
      - Auto-detect a spread column among: "spread value", "rounded_spread", "pred_spread", "spread".
        Use that column (if found) to create a new column "auto_spread". If none is found, try to extract a numeric value from the "bet" column.
        Rows with auto_spread == 0 are considered non-spread bets.
      - Ensure that "dtm" and "roi (%)" exist (defaulting to 0).
      - Convert "win probability" to numeric and "bet result" to string.
    """
    if "bet type" not in df.columns:
        if "spread_type" in df.columns:
            df["bet type"] = df["spread_type"]
        else:
            df["bet type"] = "Favorite Spreads"
    
    if "home/away" not in df.columns:
        if "bet" in df.columns:
            def infer_home_away(x):
                x = str(x).upper()
                if "HOME" in x:
                    return "Home"
                elif "AWAY" in x:
                    return "Away"
                else:
                    return "Both"
            df["home/away"] = df["bet"].apply(infer_home_away)
        elif "home team" in df.columns:
            df["home/away"] = "Home"
        else:
            df["home/away"] = "Both"
    
    # Auto-detect a spread column.
    spread_candidates = ["spread value", "rounded_spread", "pred_spread", "spread"]
    spread_col = None
    for candidate in spread_candidates:
        if candidate in df.columns:
            spread_col = candidate
            break
    if spread_col:
        df["auto_spread"] = df[spread_col].fillna(0.0)
    else:
        st.warning("No recognized spread column found. Attempting to extract numeric spread from 'bet' column.")
        if "bet" in df.columns:
            def extract_spread(text):
                m = re.search(r'(-?\d+\.?\d*)', str(text))
                if m:
                    try:
                        return float(m.group(1))
                    except:
                        return 0.0
                return 0.0
            df["auto_spread"] = df["bet"].apply(extract_spread)
        else:
            df["auto_spread"] = 0.0
    
    for col in ["dtm", "roi (%)"]:
        if col not in df.columns:
            df[col] = 0.0
    
    if "win probability" in df.columns:
        df["win probability"] = pd.to_numeric(df["win probability"], errors='coerce').fillna(0.0)
    if "bet result" in df.columns:
        df["bet result"] = df["bet result"].astype(str)
    
    return df

# ============================================================
# LOAD & PREPROCESS DATA
# ============================================================
data = load_raw_data()
data = preprocess_data(data)

# ============================================================
# STREAMLIT APP: USER INPUTS
# ============================================================
st.title("Rithmm Calculator")

include_spread = st.checkbox("Include Spread in Calculation", value=True)

# Model filter.
model = st.selectbox("Model Name", options=sorted(data["model name"].unique()))

# Bet Type filter.
# Options: OutcomeSpreadWin, OutcomeMoneylineWin, OutcomeOverWin.
bet_type_options = [
    "OutcomeSpreadWin",      # For spread bets.
    "OutcomeMoneylineWin",   # For moneyline bets.
    "OutcomeOverWin",        # For totals bets.
]
bet_type = st.selectbox("Bet Type", options=bet_type_options)

# For OutcomeSpreadWin bets, add a dropdown for Spread Outcome.
spread_outcome = None
if bet_type == "OutcomeSpreadWin":
    spread_outcome = st.selectbox("Spread Outcome", options=["Favorite", "Underdog", "Both"])

# For OutcomeOverWin bets, add a dropdown for Totals Outcome.
totals_outcome = None
if bet_type == "OutcomeOverWin":
    totals_outcome = st.selectbox("Totals Outcome", options=["Over", "Under"])

# For OutcomeMoneylineWin bets, add a dropdown for Favorite/Underdog.
fav_underdog = None
if bet_type == "OutcomeMoneylineWin":
    fav_underdog = st.selectbox("Favorite/Underdog", options=["Favorite", "Underdog"])

# Home/Away filter (applies to all but totals bets).
if bet_type != "OutcomeOverWin":
    home_away = st.selectbox("Home/Away/Both", options=["Home", "Away", "Both"])
else:
    home_away = "Both"

win_prob_range = st.slider("Win Probability Range (%)", 0, 100, (0, 100), step=1)
dtm_range = st.slider("DTM Range (%)", -100, 100, (-100, 100), step=1)

st.markdown("---")

# ============================================================
# DATA FILTERING
# ============================================================
filtered_data = data.copy()

# 1) Filter by Model.
filtered_data = filtered_data[filtered_data["model name"] == model]

# 2) Filter by Bet Type.
if bet_type == "OutcomeSpreadWin":
    # Include only rows where auto_spread is nonzero.
    filtered_data = filtered_data[filtered_data["auto_spread"] != 0]
elif bet_type == "OutcomeOverWin":
    # For totals bets, we don't filter by bet type directly.
    pass
elif bet_type == "OutcomeMoneylineWin":
    # We'll handle moneyline filtering below.
    pass
else:
    filtered_data = filtered_data[filtered_data["bet type"] == bet_type]

# 3) Filter by Home/Away (if applicable).
if bet_type != "OutcomeOverWin" and home_away != "Both":
    filtered_data = filtered_data[filtered_data["home/away"].str.contains(home_away, case=False, na=False)]

# 4) For OutcomeSpreadWin, apply the Spread Outcome filter.
if bet_type == "OutcomeSpreadWin" and spread_outcome is not None:
    if spread_outcome == "Favorite":
        filtered_data = filtered_data[filtered_data["auto_spread"] < 0]
    elif spread_outcome == "Underdog":
        filtered_data = filtered_data[filtered_data["auto_spread"] > 0]
    # "Both" means no additional filtering.

# 5) For OutcomeOverWin, apply Totals Outcome filter.
if bet_type == "OutcomeOverWin" and totals_outcome is not None:
    if "pred_total_winner" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["pred_total_winner"].str.contains(totals_outcome, case=False, na=False)]
    elif "bet" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["bet"].str.contains(totals_outcome, case=False, na=False)]

# 6) For OutcomeMoneylineWin, apply custom filtering.
if bet_type == "OutcomeMoneylineWin" and fav_underdog is not None:
    if fav_underdog == "Favorite":
        filtered_data = filtered_data[filtered_data["win probability"] > 50]
    else:
        filtered_data = filtered_data[filtered_data["win probability"] <= 50]

# 7) Apply Win Probability Range filter.
if "win probability" in filtered_data.columns:
    filtered_data = filtered_data[
        (filtered_data["win probability"] >= win_prob_range[0]) &
        (filtered_data["win probability"] <= win_prob_range[1])
    ]

# 8) Apply DTM Range filter.
if "dtm" in filtered_data.columns:
    filtered_data = filtered_data[
        (filtered_data["dtm"] >= dtm_range[0]) &
        (filtered_data["dtm"] <= dtm_range[1])
    ]

# 9) If not including spread, force auto_spread to 0.
if not include_spread:
    filtered_data["auto_spread"] = 0.0

# ============================================================
# CALCULATE METRICS
# ============================================================
total_bets = len(filtered_data)
total_wins = filtered_data["bet result"].value_counts().get("WIN", 0)
total_losses = total_bets - total_wins
win_percentage = (total_wins / total_bets * 100) if total_bets > 0 else 0

st.subheader("Results")
st.write("**Total Bets:**", total_bets)
st.write("**Total Wins:**", total_wins)
st.write("**Total Losses:**", total_losses)
st.write("**Win Percentage:**", f"{win_percentage:.2f}%")

# ============================================================
# SMART BET LOGIC
# ============================================================
is_smart_bet = False
if bet_type in ["OutcomeSpreadWin", "OutcomeOverWin"]:
    if total_bets >= 10 and win_percentage >= 60:
        is_smart_bet = True
    elif 4 <= total_bets < 10 and win_percentage >= 70:
        is_smart_bet = True
elif bet_type == "OutcomeMoneylineWin":
    if fav_underdog == "Underdog":
        if (win_percentage >= 50) or (filtered_data["roi (%)"].mean() >= 10):
            is_smart_bet = True
    elif fav_underdog == "Favorite":
        if (win_percentage >= 65) or (filtered_data["roi (%)"].mean() >= 10):
            is_smart_bet = True

if is_smart_bet:
    st.success("Smart Bet!")
else:
    st.info("Not a Smart Bet")

# ============================================================
# OUTPUT FILTERED DATA (OPTIONAL)
# ============================================================
if st.checkbox("Show Filtered Data"):
    st.dataframe(filtered_data)

st.markdown("---")
st.info("""
Note:
- For OutcomeSpreadWin bets, 'Favorite' filters for negative spreads and 'Underdog' for positive spreads.
- Rows with auto_spread == 0 are assumed not to be spread bets.
- OutcomeOverWin bets are filtered using the Totals Outcome dropdown.
- OutcomeMoneylineWin bets: 'Favorite' means win probability > 50%; 'Underdog' means ≤ 50%.
""")
