import pandas as pd, numpy as np
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',500)
df = pd.read_pickle('./clean2.pkl')
SHORT={'Terry Rozier Parlays':'Rozier','Big Money$':'BigMoney','Jebron Lames - S/ML':'Jebron'}
df['M']=df['model'].map(SHORT)
df=df.dropna(subset=['win probability'])

print('### juice composition of spread bets')
s=df[df.market=='Spread']
print(s['payout (american)'].value_counts().sort_index().to_string())
print()
print('spread: odds vs role/side crosstab of ROI')
s2=s.copy(); s2['jb']=np.where(s2['payout (american)']>=-110,'-110 or better','-111 to -122')
print(s2.groupby(['jb','role']).apply(lambda x: pd.Series(dict(n=len(x),WR=round(x['win'].sum()/max(x['decided'].sum(),1)*100,1),ROI=round(x['units'].mean()*100,2))),include_groups=False).to_string())
print()
print('### totals juice')
t=df[df.market=='Total']
print(t['payout (american)'].value_counts().sort_index().to_string())
print()

print('#'*95); print('TIME-SPLIT STABILITY (each model split at its own median game date)'); print('#'*95)
def stab(mask_desc, mask):
    rows=[]
    for m in ['BigMoney','Jebron','Rozier','ALL']:
        g = df[mask] if m=='ALL' else df[mask & (df.M==m)]
        if len(g)<10: continue
        cut=g['gt'].median()
        a=g[g['gt']<=cut]; b=g[g['gt']>cut]
        rows.append(dict(model=m,n=len(g),ROI=round(g['units'].mean()*100,2),
          n1=len(a),ROI1=round(a['units'].mean()*100,2) if len(a) else None,
          n2=len(b),ROI2=round(b['units'].mean()*100,2) if len(b) else None))
    print(f'-- {mask_desc}')
    print(pd.DataFrame(rows).to_string(index=False)); print()

sp=df.market=='Spread'; ml=df.market=='Moneyline'; to=df.market=='Total'
stab('SPREAD underdogs (spread value > 0)', sp & (df.role=='Underdog'))
stab('SPREAD favorites', sp & (df.role=='Favorite'))
stab('SPREAD at -110 or better', sp & (df['payout (american)']>=-110))
stab('SPREAD at -111 to -122', sp & (df['payout (american)']<-110))
stab('SPREAD dogs at -110 or better', sp & (df.role=='Underdog') & (df['payout (american)']>=-110))
stab('SPREAD line 5-13.5 abs', sp & df['spread value'].abs().between(5,13.5))
stab('ML DTM 5-20', ml & df.dtm.between(5,20))
stab('ML odds +200..+300', ml & df['payout (american)'].between(200,300))
stab('ML home', ml & (df.venue=='Home'))
stab('TOTAL Recommended (DTM>0)', to & (df.dtm>0))
stab('ALL Recommended (DTM>0)', df.dtm>0)
stab('ALL Caution (DTM<=0)', df.dtm<=0)

print('#'*95); print('CLUSTER BOOTSTRAP 95% CI on ROI (resample games)'); print('#'*95)
rng=np.random.default_rng(7)
def boot(desc, g, B=4000):
    if len(g)<15: return
    games=g['gid'].unique(); byg={k:v['units'].values for k,v in g.groupby('gid')}
    obs=g['units'].mean()*100; out=[]
    for _ in range(B):
        pick=rng.choice(games,len(games),replace=True)
        v=np.concatenate([byg[p] for p in pick])
        out.append(v.mean()*100)
    lo,hi=np.percentile(out,[2.5,97.5])
    print(f'{desc:46s} n={len(g):4d}  ROI={obs:+6.2f}%  95% CI [{lo:+6.2f}, {hi:+6.2f}]  P(ROI>0)={np.mean(np.array(out)>0):.2f}')
boot('ALL BETS', df)
boot('Spread underdogs (all models)', df[sp&(df.role=='Underdog')])
boot('Spread dogs @ -110 or better', df[sp&(df.role=='Underdog')&(df['payout (american)']>=-110)])
boot('Spread @ -110 or better (all)', df[sp&(df['payout (american)']>=-110)])
boot('Spread line 5-13.5', df[sp&df['spread value'].abs().between(5,13.5)])
boot('BigMoney spreads', df[sp&(df.M=='BigMoney')])
boot('Rozier spread dogs', df[sp&(df.role=='Underdog')&(df.M=='Rozier')])
boot('ML DTM 5-20 (all models)', df[ml&df.dtm.between(5,20)])
boot('ML odds +200..+300', df[ml&df['payout (american)'].between(200,300)])
boot('ML home (all models)', df[ml&(df.venue=='Home')])
boot('Recommended (DTM>0) all markets', df[df.dtm>0])
boot('Rozier ML (worst cell)', df[ml&(df.M=='Rozier')])
