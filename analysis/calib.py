import pandas as pd, numpy as np
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',500)
df = pd.read_pickle('./clean2.pkl')
SHORT={'Terry Rozier Parlays':'Rozier','Big Money$':'BigMoney','Jebron Lames - S/ML':'Jebron'}
df['M']=df['model'].map(SHORT)
d=df[df.decided==1]

print('#'*95); print('CALIBRATION: model predicted win% vs actual win%, and vs market implied%'); print('#'*95)
for m in ['BigMoney','Jebron','Rozier']:
    print('\n---',m)
    g=d[d.M==m].copy()
    g['dec10']=pd.qcut(g['win probability'],10,duplicates='drop')
    t=g.groupby('dec10',observed=True).apply(lambda x: pd.Series(dict(
        n=len(x), pred=round(x['win probability'].mean(),1),
        mkt=round(x['implied_pct'].mean(),1), actual=round(x['win'].mean()*100,1),
        model_err=round(x['win'].mean()*100-x['win probability'].mean(),1),
        mkt_err=round(x['win'].mean()*100-x['implied_pct'].mean(),1),
        ROI=round(x['units'].mean()*100,2))), include_groups=False)
    print(t.to_string())

print()
print('#'*95); print('WHO IS SHARPER? Brier / log-loss: model vs market (all decided bets)'); print('#'*95)
for m in ['BigMoney','Jebron','Rozier','ALL']:
    g = d if m=='ALL' else d[d.M==m]
    y=g['win'].values; p=np.clip(g['win probability'].values/100,1e-6,1-1e-6); q=np.clip(g['implied_pct'].values/100,1e-6,1-1e-6)
    print(f'{m:9s} n={len(g):5d}  Brier model={np.mean((p-y)**2):.4f}  market={np.mean((q-y)**2):.4f}   '
          f'LogLoss model={-np.mean(y*np.log(p)+(1-y)*np.log(1-p)):.4f} market={-np.mean(y*np.log(q)+(1-y)*np.log(1-q)):.4f}')

print()
print('#'*95); print('SAME, SPLIT BY MARKET'); print('#'*95)
for mk in ['Moneyline','Spread','Total']:
    for m in ['BigMoney','Jebron','Rozier']:
        g=d[(d.M==m)&(d.market==mk)]
        if len(g)<20: continue
        y=g['win'].values; p=np.clip(g['win probability'].values/100,1e-6,1-1e-6); q=np.clip(g['implied_pct'].values/100,1e-6,1-1e-6)
        print(f'{mk:10s} {m:9s} n={len(g):4d} Brier model={np.mean((p-y)**2):.4f} market={np.mean((q-y)**2):.4f} diff={np.mean((p-y)**2)-np.mean((q-y)**2):+.4f}')
    print()
