# Backtest analysis

Reproducible breakdown of the three Rithmm model exports in the repo root
(`32529 rozier copy.xlsx`, `32925 big money copy.xlsx`, `32925 Hebron lames copy.xlsx`).

Run from the repo root, in order — each script writes a pickle the next one reads:

| Script | What it does |
|---|---|
| `prep.py`   | Concatenates the three `in` sheets, drops ungraded rows and 23 exact duplicates, derives implied probability, units, favorite/underdog and Recommended/Caution. Writes `clean.pkl`. |
| `scan.py`   | Adds the DTM / win-probability / price / spread / total bands and scans ~2,800 slices. Writes `clean2.pkl` and `scan.pkl`. |
| `tables.py` | Prints the headline breakdown tables (model × market × side × role × band). |
| `calib.py`  | Calibration by decile, plus Brier and log-loss for model vs. market. |
| `robust.py` | Cross-model consistency: same bucket, how many of the three models profited. |
| `stab.py`   | First-half / second-half stability and cluster-bootstrap CIs (resampled by game). |
| `final.py`  | Real-money staking results and the per-model stable-slice playbook. |
| `export.py` | Emits `data.json` for the edge sheet. |

`edge-sheet.html` is the self-contained report built from `data.json`
(published at https://claude.ai/artifact/EjF7uQxMczocycU4Utbz1t).

Requires `pandas`, `numpy`, `openpyxl`.

## Field notes

- **DTM** is `(model win% ÷ market implied win% − 1) × 100` — the model's edge as a
  percentage of the market's own price, vig included. Confirmed against every row.
- **`spread value`** is the spread applied to the side actually bet: negative lays
  points, positive takes them. Re-deriving cover from the final scores matches the
  recorded `bet result` on 100% of spread rows (same for totals and moneylines).
- **`amount bet`** is the real stake in units; 703 rows are 0, i.e. tracked but not played.
- ROI is flat 1 unit per bet: a win returns `decimal odds − 1`, a loss −1, a push 0,
  and pushes stay in the denominator.
