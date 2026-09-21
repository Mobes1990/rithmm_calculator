import pandas as pd, numpy as np
from math import comb
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',500)
df = pd.read_pickle('./clean2.pkl')
SHORT={'Terry Rozier Parlays':'Rozier','Big Money$':'BigMoney','Jebron Lames - S/ML':'Jebron'}
df['M']=df['model'].map(SHORT)

def st(g):
    dec=g['decided'].sum(); w=g['win'].sum()
    return dict(n=len(g), W=int(w), L=int(dec-w), WR=round(w/dec*100,1) if dec else 0,
                U=round(g['units'].sum(),2), ROI=round(g['units'].mean()*100,2))

DIMS = [('b_dtm','DTM band'),('b_wp','Win-prob band'),('b_odds','Odds band'),
        ('b_spread','Spread band'),('b_total','Total band'),
        ('role','Fav/Dog'),('venue','Home/Away'),('ou','Over/Under'),('flag','Rec/Caution')]

print('#'*100); print('CROSS-MODEL CONSISTENCY: same market+dimension bucket, per model'); print('#'*100)
out=[]
for market in ['Moneyline','Spread','Total']:
    d1=df[df.market==market]
    for dim,dl in DIMS:
        if d1[dim].nunique()<=1: continue
        for bv,g in d1.groupby(dim):
            if bv in ('n/a','nan') or len(g)<25: continue
            per={}
            for m in ['BigMoney','Jebron','Rozier']:
                gm=g[g.M==m]
                per[m]=st(gm) if len(gm)>=8 else None
            tot=st(g)
            pos=sum(1 for m,v in per.items() if v and v['ROI']>0)
            cov=sum(1 for v in per.values() if v)
            out.append(dict(market=market, dim=dl, bucket=str(bv), n=tot['n'], WR=tot['WR'],
                ROI=tot['ROI'], U=tot['U'], models_pos=f'{pos}/{cov}',
                **{f'{m}': (f"{per[m]['ROI']:+.1f}% ({per[m]['n']})" if per[m] else '-') for m in ['BigMoney','Jebron','Rozier']}))
O=pd.DataFrame(out).sort_values(['market','dim','bucket'])
print(O.to_string(index=False))
O.to_pickle('./consistency.pkl')
