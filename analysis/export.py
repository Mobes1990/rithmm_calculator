import pandas as pd, numpy as np, json
df = pd.read_pickle('./clean2.pkl').dropna(subset=['win probability'])
SHORT={'Terry Rozier Parlays':0,'Big Money$':1,'Jebron Lames - S/ML':2}
MK={'Moneyline':0,'Spread':1,'Total':2}
SIDE={'Home':0,'Away':1,'Over':2,'Under':3,'n/a':4}
ROLE={'Favorite':0,'Underdog':1,'Pickem':2,'n/a':3}
RES={'WIN':1,'LOSS':0,'PUSH':2}
df=df.sort_values('gt')
rows=[]
for _,r in df.iterrows():
    side = r['ou'] if r['market']=='Total' else r['venue']
    rows.append([
        SHORT[r['model']], MK[r['market']], SIDE.get(side,4), ROLE.get(r['role'],3),
        round(float(r['dtm']),2), round(float(r['win probability']),2),
        int(r['payout (american)']), round(float(r['dec']),4),
        None if pd.isna(r['spread value']) else float(r['spread value']),
        None if pd.isna(r['totals value']) else float(r['totals value']),
        RES[r['bet result']], round(float(r['units']),4), round(float(r['breakeven']),2),
        str(pd.Timestamp(r['gt']).date()), r['home team'], r['away team'],
        round(float(r['amount bet']),2),
    ])
meta=dict(
  models=['Terry Rozier Parlays','Big Money$','Jebron Lames - S/ML'],
  markets=['Moneyline','Spread','Total'],
  sides=['Home','Away','Over','Under','n/a'],
  roles=['Favorite','Underdog','Pickem','n/a'],
  fields=['m','k','s','r','dtm','wp','odds','dec','spr','tot','res','u','be','date','home','away','stake'])
open('./data.json','w').write(json.dumps({'meta':meta,'rows':rows},separators=(',',':')))
print('rows',len(rows))
import os; print('bytes', os.path.getsize('./data.json'))
