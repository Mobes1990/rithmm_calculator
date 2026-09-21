import pandas as pd, numpy as np, json
df = pd.read_pickle('analysis/cfb_clean.pkl')
df = df[~df.degenerate].sort_values('gt')
MODELS=['ATS','Defensive Total','Turnover and Win Probability','Rithmm AI']
MI={m:i for i,m in enumerate(MODELS)}
MK={'Moneyline':0,'Spread':1,'Total':2}
SIDE={'Home':0,'Away':1,'Over':2,'Under':3,'n/a':4}
ROLE={'Favorite':0,'Underdog':1,'Pickem':2,'n/a':3}
RES={'WIN':1,'LOSS':0,'PUSH':2}
rows=[]
for _,r in df.iterrows():
    side = r['ou'] if r['market']=='Total' else r['venue']
    rows.append([MI[r['model']], MK[r['market']], SIDE.get(side,4), ROLE.get(r['role'],3),
      round(float(r['DTM']),2), round(float(r['Win Probability']),2), int(r['am']),
      round(float(r['dec']),4),
      None if pd.isna(r['Spread Value']) else float(r['Spread Value']),
      None if pd.isna(r['Totals Value']) else float(r['Totals Value']),
      RES[r['Bet Result']], round(float(r['units']),4), round(float(r['imp']),2),
      str(pd.Timestamp(r['gt']).date()), r['Home Team'], r['Away Team'],
      1 if r['Recommended Bet'] else 0])
out={'meta':{'models':MODELS,'short':['ATS','Defensive Total','Turnover + WP','Rithmm AI'],
     'markets':['Moneyline','Spread','Total'],'sport':'CFB'},'rows':rows}
open('analysis/cfb_data.json','w').write(json.dumps(out,separators=(',',':')))
import os; print('rows',len(rows),'bytes',os.path.getsize('analysis/cfb_data.json'))
