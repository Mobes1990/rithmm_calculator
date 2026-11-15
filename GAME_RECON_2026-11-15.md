# Game Recon: NBA, Sunday Nov 15, 2026

Prepared in a cloud session (no access to the PC, the Rithmm app, or live model outputs) as a handoff for the PC Claude agent.

**What this covers:**
1. What the three backtest files in this repo say about where each model has an edge.
2. Bugs in `rithmm_calculator.py` that make its "Smart Bet" output unreliable.
3. Tonight's slate: lines and injuries, taken from search snippets.
4. How the backtest filters map onto tonight's games, plus a to-do list for the PC agent.

> **Caveats.** The backtest is small: 1,833 graded NBA bets from Nov 2024 to Mar 2025. Most splits have fewer than 100 bets, and only a few are statistically meaningful (z-scores are given where it matters). Tonight's lines and injuries come from search-result snippets. The source pages themselves (dimers.com, talkbasket.net) couldn't be fetched from this session, and the sources disagreed with each other in places. **Re-check every line and injury status against a live board and the official NBA injury report before acting.**

---

## 1. Backtest findings (from the 3 `.xlsx` files, sheet `in`)

**Data shape:** Each file has 25 columns, all NBA, and 99% of lines are "Consensus". Model names in the raw files are `Terry Rozier Parlays`, `Big Money$` and `Jebron Lames - S/ML`. The calculator overwrites these with short names. The `bet` column only ever contains `HOME`, `AWAY`, `OVER` or `UNDER`. `spread value` is from the perspective of the side being bet: negative means a favorite, positive means an underdog. I verified this: actual cover matches `bet result` on 100% of non-push rows. Results: 925 W / 895 L / 13 PUSH.

**Date coverage:** BigMoney and Rozier cover Feb–Mar 2025 only. Jebron Lames covers Nov 2024 to Mar 2025.

ROI below is per 1-unit flat bet at the listed decimal payout. Break-even at -110 is 52.4%.

### Overall by model and bet type

| Model | Spread (n / win% / ROI) | Moneyline | Totals |
|---|---|---|---|
| BigMoney | 154 / 54.5% / **+5.4%** | 159 / 50.9% / **+12.0%** | 157 / 50.3% / -3.2% |
| Jebron Lames | 250 / 51.6% / +0.9% | 239 / 43.9% / +1.2% | 270 / 53.0% / +1.5% |
| Terry Rozier | 207 / 52.2% / +0.6% | 197 / 49.2% / -4.9% | 200 / 49.5% / -5.0% |

### The strongest signal: spread underdogs beat spread favorites in every model

| Split (all models pooled) | n | Win% | ROI | z vs. break-even |
|---|---|---|---|---|
| Spread **underdogs** (any size) | 387 | **56.3%** | **+7.4%** | 1.55 |
| Spread favorites (any size) | 214 | 48.1% | -8.1% | -1.24 |
| **Small dogs, +0.5 to +3** | 75 | **64.0%** | **+21.9%** | **2.01** |
| **Small favorites, -0.5 to -3** | 37 | **27.0%** | **-48.5%** | **-3.08** |

Spread side by model:
- **BigMoney:** dogs 58.1% (+12.0%), favorites 49.2% (-4.5%).
- **Terry Rozier:** dogs 57.0% (+10.4%), favorites 41.5% (-20.8%). Fade Rozier spread favorites.
- **Jebron Lames:** dogs 51.6%, favorites 51.7%. Neutral overall, but **Jebron AWAY spread** is 60.7% (+19.3%, n=56) while Jebron HOME spread is 49.0% (-4.5%, n=194).

**Takeaway:** When a model's spread pick is a short underdog (+0.5 to +3), that has been the best spot in the data. When its spread pick is a short favorite (-0.5 to -3), it has been the worst. This pattern holds in all three models individually.

### Moneyline
- BigMoney is the only model with consistently positive moneyline ROI: +12.0% overall, with both favorites and underdogs positive.
- Rozier away moneyline underdogs: 22.6% win rate, -21.5% ROI (n=62). Avoid. Rozier home moneyline underdogs: +21.0% ROI (n=39).
- Rozier home moneyline favorites: -22.2% ROI (n=34).

### Totals
- **Rozier OVER:** 58.5%, +13.1% ROI (n=65). **Rozier UNDER:** 45.2%, -13.7% (n=135). Rozier mostly picks unders, which is its weak side.
- Jebron UNDER: 53.8%, +2.7% (n=184). Small positive edge; best at DTM 5–10, 62.9% (n=35).
- BigMoney totals: about flat. No edge.

### When the models agree (same game, same market, same side)

| Market | 1 model only | 2 models agree | All 3 agree |
|---|---|---|---|
| Spread | 50.6% / -1.7% | **55.8% / +7.7%** (n=86) | 52.8% / +3.5% (n=36) |
| Moneyline | 43.1% / -9.5% | **54.2% / +16.2%** (n=96) | 48.5% / +3.0% (n=33) |
| Totals | 50.4% / -3.7% | 54.7% / +4.4% (n=86) | 46.9% / -7.3% (n=32) |

Two models agreeing has been the best tier. Full three-model consensus has *not* added anything, probably because those are heavily-bet chalk sides.

### Win probability and DTM
- Spread win probabilities cluster tightly at 50–60%, so the win-probability slider barely separates spread bets.
- No DTM bucket is consistently good across models. Single-model buckets such as BigMoney spread at DTM 10–20 (75%, n=12) are too small to trust.
- Note: in 36% of spread rows, the model's own predicted scores do *not* cover the spread it's betting. The pick logic isn't simply "predicted margin beats the line". Worth asking about or investigating.

---

## 2. Bugs in `rithmm_calculator.py` (fix these before trusting "Smart Bet!")

1. **The moneyline filter doesn't restrict to moneyline bets.** For `OutcomeMoneylineWin`, the code never filters on `bet type`. "Favorite" then becomes *every* row with win probability > 50, which includes spread and totals rows. Example: BigMoney + ML + Favorite returns 380 rows, of which only 71 are moneyline bets. Fix: `filtered_data = filtered_data[filtered_data["bet type"] == "OutcomeMoneylineWin"]`.
2. **Moneyline favorite/underdog is defined by win probability, not price.** 35 rows have win probability > 50 at plus money, and 21 rows have ≤ 50 at minus money. Use `payout (american) < 0` for favorite instead.
3. **The `roi (%)` column doesn't exist in the files.** It defaults to 0, so the "ROI ≥ 10%" Smart Bet condition for moneylines can never fire. Compute ROI from `payout (decimal)` instead: a win pays `decimal - 1`, a loss costs `-1`, a push is `0`.
4. **Pushes count as losses.** `total_losses = total_bets - total_wins`. There are 13 pushes in the data.
5. **The totals filter relies on `bet` containing "Over"/"Under".** That works, but there's no explicit `bet type == OutcomeOverWin` filter. Add one for safety.
6. **"Include Spread in Calculation" does nothing.** It zeroes `auto_spread` *after* all the filtering is done.
7. **The DTM slider is capped at ±100,** but 19 rows exceed that (max 819). Those rows are always silently excluded.
8. **The file paths are hard-coded** to `C:\Users\sarah\OneDrive\...`. Consider making them relative to the script folder, since the xlsx files live next to it in this repo.
9. **Suggested additions:** a spread-size filter (e.g. dog +0.5 to +3) and an ROI display, since ROI is where the edges actually show up.

---

## 3. Tonight's slate (Sun Nov 15, 2026): lines from search snippets

Books disagree by up to a point. Verify on a live board.

| Game | Spread | Total | Moneyline / notes |
|---|---|---|---|
| Pacers @ 76ers | PHI -7.5 (DK: PHI -102 / IND +7.5 -118) | 224.5 | Embiid **OUT**. Nembhard (IND) questionable |
| Mavericks @ Celtics | BOS -14.5 (-105) | ? | |
| Lakers @ Suns | LAL -2.5 (-115) | 227.5 | Reaves **OUT** (heel), Luka **day-to-day** (ankle). PHX: Mark Williams out (shoulder) |
| Knicks @ Raptors | NYK -4.5 (-110) | 217.5 | TOR: Scottie Barnes questionable (groin). Sources conflict on Kawhi Leonard. Verify |
| Hawks @ Bucks | ATL -6.5 (-115) at BangTheBook, -7.5 at FanDuel | 232.5–233.5 | ATL -287 / MIL +234. MIL reportedly 1-12; Dieng out. ATL has 5 players on the report |
| Rockets @ Wizards | HOU -8.5 (Novig) to -9.5 (FanDuel) | 222.5 | Dimers model: HOU 115-107, WAS covers 53.8%. Capela status conflicts; Steven Adams probable |
| Hornets @ Clippers | LAC -1.5 | 215.5 | LAC -116 / CHA -102. LAC: Ingram out, Beal out. CHA: Knueppel out |
| Spurs @ Jazz | SAS -16.5 | 223.5 | SAS -1500 / UTA +870. Dimers likes UTA +16.5 |
| Thunder vs ? (possibly @ Kings) | OKC -10.5 | 221.5 | Opponent and line unconfirmed |

---

## 4. How the backtest maps onto tonight

These are candidate *spots*, not picks. They only matter if a Rithmm model actually takes the side in question tonight.

- **Short-dog spots (+0.5 to +3), historically the best bucket:** **Suns +2.5** vs. Lakers, and **Hornets +1.5** at Clippers. If BigMoney or Rozier (ideally both) take PHX or CHA against the spread, that matches the strongest pattern in the data. The Lakers being without Reaves, with Luka day-to-day, helps the Suns case; watch whether the line moves toward pick'em.
- **Short-favorite spots, historically the worst bucket:** **Lakers -2.5** and **Clippers -1.5**. Treat any model spread pick on these as a fade or pass, especially from Rozier.
- **Big dogs:** Mavericks +14.5, Jazz +16.5, Wizards +8.5/9.5, Bucks +6.5/7.5. BigMoney and Rozier dogs of 9+ points have done well (60–61%). Jebron's big dogs have not (46%).
- **Totals:** Only act on Rozier **OVER** picks or Jebron **UNDER** picks (DTM 5–10 best). Skip Rozier unders.
- **Moneyline:** Only BigMoney has shown a moneyline edge. Avoid Rozier away underdog moneylines.

---

## 5. To-do for the PC agent

1. Open Rithmm and record tonight's picks for all three models: market, side, line, win probability, DTM.
2. Tag each pick: (a) spread dog +0.5 to +3? (b) spread favorite -0.5 to -3? (c) do two or more models agree? (d) does it fall in a model's bad split (Rozier spread favorites, Rozier unders, Rozier away ML dogs, Jebron home spreads)?
3. Re-pull live lines and the official NBA injury report: Embiid, Luka, Reaves, Barnes, Kawhi, Capela, Nembhard.
4. Fix calculator bugs #1–#4 from section 2 before relying on it. Consider adding a spread-size filter and an ROI readout.
5. Append tonight's graded results to the data, so the small-sample buckets above get bigger over time.

---

## Sources
- [Dimers: NBA best bets 11/15/2026](https://dimers.com/nba/news/nba-best-bets-11-15-2026-ac)
- [Dimers: Rockets vs. Wizards 11/15](https://www.dimers.com/nba/news/houston-rockets-vs-washington-wizards-prediction-11-15-2026-ac)
- [Dimers: Hawks vs. Bucks 11/15](https://www.dimers.com/nba/news/atlanta-hawks-vs-milwaukee-bucks-prediction-11-15-2026-ac)
- [Dimers: Mavericks vs. Celtics 11/15](https://www.dimers.com/nba/news/dallas-mavericks-vs-boston-celtics-prediction-11-15-2026-ac)
- [FanDuel Research: NBA predictions, odds 11/15](https://www.fanduel.com/research/nba-predictions-odds-11-15-2026)
- [BetMGM: Mavericks vs. Celtics props 11/15](https://sports.betmgm.com/en/blog/nba/mavericks-celtics-player-prop-bets-picks-nba-nov-15-jaa)
- [BetMGM: Lakers vs. Suns props 11/15](https://sports.betmgm.com/en/blog/nba/lakers-suns-player-prop-bets-picks-nba-nov-15-jaa)
- [BetMGM: Pacers vs. 76ers props 11/15](https://sports.betmgm.com/en/blog/nba/pacers-76ers-player-prop-bets-picks-nba-nov-15-jaa)
- [BetMGM: Pacers vs. 76ers prediction 11/15](https://sports.betmgm.com/en/blog/nba/pacers-76ers-prediction-odds-lines-picks-nba-nov-15-jaa)
- [SI: Pacers vs. 76ers 11/15](https://www.si.com/betting/pacers-vs-76ers-prediction-odds-and-best-nba-prop-bets-for-sunday-nov-15-2026)
- [Yahoo: Spurs vs. Jazz 11/15](https://sports.yahoo.com/articles/spurs-vs-jazz-prediction-pick-125907839.html)
- [Yahoo: Rockets vs. Wizards injury report 11/15](https://sports.yahoo.com/articles/november-15th-injury-report-houston-005119347.html)
- [BangTheBook: Hawks vs. Bucks 11/15](https://bangthebook.com/atlanta-hawks-vs-milwaukee-bucks-prediction-2026-11-15/)
- [BangTheBook: Knicks vs. Raptors 11/15](https://bangthebook.com/new-york-knicks-vs-toronto-raptors-prediction-2026-11-15/)
- [TalkBasket: NBA injury report 11/15](https://www.talkbasket.net/228284-nba-injury-report-embiid-reaves-out-on-sunday-november-15)
- [Heavy: Raptors injury report vs. Knicks 11/15](https://heavy.com/sports/nba/toronto-raptors/injury-report-vs-knicks-november-15/)
- [iHeart: Lakers vs. Suns injury report](https://sportssd.iheart.com/content/2026-11-15-lakers-vs-suns-injury-report-nov-15/)
- [iHeart: Hornets vs. Clippers injury report](https://sportssd.iheart.com/content/2026-11-15-hornets-vs-clippers-injury-report-nov-15/)
- [iHeart: Hawks vs. Bucks injury report](https://foxsports1070.iheart.com/content/2026-11-15-hawks-vs-bucks-injury-report-nov-15/)
- [Covers: NBA injuries](https://www.covers.com/sport/basketball/nba/injuries) · [ESPN: NBA injuries](https://www.espn.com/nba/injuries)
