"""Clean the CFB tracked-bets export and derive the analysis fields."""
import pandas as pd, numpy as np, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "rithmm-tracked-bets-2026-09-21.csv"
df = pd.read_csv(SRC)

def money(s):
    return pd.to_numeric(s.astype(str).str.replace(r"[\$,]", "", regex=True), errors="coerce")

df["am"]    = money(df["Payout (American)"])
df["stake"] = money(df["Amount Bet"])
df["dec"]   = df["Payout (Decimal)"]
df["gt"]    = pd.to_datetime(df["Date"])
df["gid"]   = df["Date"] + "|" + df["Home Team"] + "|" + df["Away Team"]

before = len(df)
key = ["gid","Model Name","Bet Type","Bet","Spread Value","Totals Value","am","Win Probability"]
df = df.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
print(f"dropped exact duplicates: {before-len(df)} -> {len(df)}")

# Degenerate rows: the model saturated, or the price is a formality. They carry no
# information about edge and they distort every average they land in.
df["degenerate"] = (df["Win Probability"] >= 99) | (df["Win Probability"] <= 1) \
                 | (df["am"] <= -2000) | (df["am"] >= 2000)
print(f"degenerate rows flagged: {int(df['degenerate'].sum())}")

df["imp"] = np.where(df["am"] > 0, 100/(df["am"]+100), -df["am"]/(-df["am"]+100)) * 100

# This export's DTM is edge as a share of the headroom above the market price:
#   DTM = (win% - implied%) / (100 - implied%) * 100
# (The older NBA workbooks use a different definition: win%/implied% - 1.)
df["dtm_check"] = (df["Win Probability"] - df["imp"]) / (100 - df["imp"]) * 100
df["stale_price"] = (df["dtm_check"] - df["DTM"]).abs() > 0.05
print(f"rows whose DTM disagrees with the posted price (line moved): {int(df['stale_price'].sum())}")

res = df["Bet Result"]
df["win"]     = (res == "WIN").astype(int)
df["push"]    = (res == "PUSH").astype(int)
df["decided"] = (res != "PUSH").astype(int)
df["units"]   = np.where(res == "WIN", df["dec"]-1, np.where(res == "LOSS", -1.0, 0.0))

MARKET = {"OutcomeMoneylineWin":"Moneyline","OutcomeSpreadWin":"Spread","OutcomeOverWin":"Total"}
df["market"] = df["Bet Type"].map(MARKET)
df["venue"]  = np.where(df["market"]=="Total", "n/a", df["Bet"].str.title())
df["ou"]     = np.where(df["market"]=="Total", df["Bet"].str.title(), "n/a")

def role(r):
    if r["market"] == "Moneyline":
        return "Underdog" if r["am"] > 0 else "Favorite"
    if r["market"] == "Spread":
        if r["Spread Value"] > 0: return "Underdog"
        if r["Spread Value"] < 0: return "Favorite"
        return "Pickem"
    return "n/a"
df["role"] = df.apply(role, axis=1)

df["flag"]      = np.where(df["Recommended Bet"], "Recommended", "Caution")
df["breakeven"] = df["imp"]
df["model"]     = df["Model Name"]

df.to_pickle("analysis/cfb_clean.pkl")

clean = df[~df.degenerate]
print()
print(df.groupby(["model","market"]).apply(lambda x: pd.Series(dict(
    n=len(x), W=int(x.win.sum()), L=int(x.decided.sum()-x.win.sum()),
    WR=round(x.win.sum()/max(x.decided.sum(),1)*100,1),
    U=round(x.units.sum(),2), ROI=round(x.units.mean()*100,2))), include_groups=False).to_string())
print()
print("ALL        :", len(df), "bets", round(df.units.sum(),2), "u", round(df.units.mean()*100,2), "%")
print("ex-degenerate:", len(clean), "bets", round(clean.units.sum(),2), "u", round(clean.units.mean()*100,2), "%")
