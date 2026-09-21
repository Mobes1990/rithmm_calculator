import pandas as pd, numpy as np, itertools
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',500)
df = pd.read_pickle('analysis/cfb_clean.pkl'); df=df[~df.degenerate].copy()
SH={'ATS':'ATS','Defensive Total':'DefTotal','Turnover and Win Probability':'TurnoverWP','Rithmm AI':'RithmmAI'}
df['M']=df['model'].map(SH); MODELS=['ATS','DefTotal','TurnoverWP','RithmmAI']
df['week']=df['gt'].dt.isocalendar().week.astype(int)
print('weeks:'); print(df.groupby('week').agg(n=('win','size'),u=('units','sum')).round(1).to_string()); print()

def st(g):
    dec=g['decided'].sum(); w=g['win'].sum()
    return dict(n=len(g),W=int(w),L=int(dec-w),WR=round(w/dec*100,1) if dec else 0,
                U=round(g['units'].sum(),2),ROI=round(g['units'].mean()*100,2))

def check(desc, g):
    if len(g)<15: print(f'{desc:52s} n={len(g)} (too thin)'); return
    s=st(g)
    per=[]
    for m in MODELS:
        gm=g[g.M==m]
        per.append(f'{m} {st(gm)["ROI"]:+.0f}%({len(gm)})' if len(gm)>=10 else f'{m} -')
    pos=sum(1 for m in MODELS if len(g[g.M==m])>=10 and st(g[g.M==m])['ROI']>0)
    cov=sum(1 for m in MODELS if len(g[g.M==m])>=10)
    wk=g.groupby('week')['units'].mean()*100
    wkstr=' '.join(f'{v:+.0f}' for v in wk.values)
    print(f'{desc:52s} n={s["n"]:4d} {s["W"]}-{s["L"]} {s["WR"]:5.1f}% {s["U"]:+7.1f}u {s["ROI"]:+7.2f}%  models {pos}/{cov}  wk[{wkstr}]')
    print(f'{"":52s} {" · ".join(per)}')

print('#'*130); print('CONSISTENCY ACROSS MODELS AND WEEKS'); print('#'*130)
mk=df.market
check('ALL BETS', df)
check('Recommended flag = TRUE', df[df.flag=='Recommended'])
check('Recommended flag = FALSE', df[df.flag=='Caution'])
print()
check('TOTALS — all', df[mk=='Total'])
check('TOTALS — OVER', df[(mk=='Total')&(df.ou=='Over')])
check('TOTALS — UNDER', df[(mk=='Total')&(df.ou=='Under')])
check('TOTALS — Recommended', df[(mk=='Total')&(df.flag=='Recommended')])
check('TOTALS — OVER + Recommended', df[(mk=='Total')&(df.ou=='Over')&(df.flag=='Recommended')])
check('TOTALS — OVER, line under 50', df[(mk=='Total')&(df.ou=='Over')&(df['Totals Value']<50)])
check('TOTALS — UNDER, line 50-55', df[(mk=='Total')&(df.ou=='Under')&(df['Totals Value'].between(50,55))])
print()
check('SPREADS — all', df[mk=='Spread'])
check('SPREADS — favorites', df[(mk=='Spread')&(df.role=='Favorite')])
check('SPREADS — underdogs', df[(mk=='Spread')&(df.role=='Underdog')])
check('SPREADS — HOME side', df[(mk=='Spread')&(df.venue=='Home')])
check('SPREADS — AWAY side', df[(mk=='Spread')&(df.venue=='Away')])
check('SPREADS — Recommended', df[(mk=='Spread')&(df.flag=='Recommended')])
check('SPREADS — dogs of 21.5+', df[(mk=='Spread')&(df.role=='Underdog')&(df['Spread Value'].abs()>21)])
check('SPREADS — favs of 21.5+', df[(mk=='Spread')&(df.role=='Favorite')&(df['Spread Value'].abs()>21)])
print()
check('MONEYLINE — all', df[mk=='Moneyline'])
check('MONEYLINE — favorites', df[(mk=='Moneyline')&(df.role=='Favorite')])
check('MONEYLINE — dogs +450 or longer', df[(mk=='Moneyline')&(df.am>=450)])
check('MONEYLINE — dogs +100 to +450', df[(mk=='Moneyline')&(df.am>=100)&(df.am<450)])
print()
check('ANY MARKET — HOME / OVER side', df[(df.venue=='Home')|(df.ou=='Over')])
check('ANY MARKET — AWAY / UNDER side', df[(df.venue=='Away')|(df.ou=='Under')])

print(); print('#'*130); print('CLUSTER BOOTSTRAP 95% CI ON ROI (resample whole games)'); print('#'*130)
rng=np.random.default_rng(11)
def boot(desc,g,B=4000):
    if len(g)<15: return
    games=g['gid'].unique(); byg={k:v['units'].values for k,v in g.groupby('gid')}
    obs=g['units'].mean()*100; out=np.empty(B)
    for i in range(B):
        pick=rng.choice(games,len(games),replace=True)
        out[i]=np.concatenate([byg[p] for p in pick]).mean()*100
    lo,hi=np.percentile(out,[2.5,97.5])
    print(f'{desc:44s} n={len(g):4d}  ROI={obs:+7.2f}%  95% CI [{lo:+7.2f}, {hi:+7.2f}]  P(ROI>0)={np.mean(out>0):.2f}')
boot('ALL BETS', df)
boot('Overs (all models)', df[(mk=='Total')&(df.ou=='Over')])
boot('Overs on lines under 50', df[(mk=='Total')&(df.ou=='Over')&(df['Totals Value']<50)])
boot('Totals flagged Recommended', df[(mk=='Total')&(df.flag=='Recommended')])
boot('Spread favorites', df[(mk=='Spread')&(df.role=='Favorite')])
boot('Spread home side', df[(mk=='Spread')&(df.venue=='Home')])
boot('Spreads flagged Recommended', df[(mk=='Spread')&(df.flag=='Recommended')])
boot('Moneyline dogs +450 or longer', df[(mk=='Moneyline')&(df.am>=450)])
boot('Unders on lines 50-55', df[(mk=='Total')&(df.ou=='Under')&(df['Totals Value'].between(50,55))])
