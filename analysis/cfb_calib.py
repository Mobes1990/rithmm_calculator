import pandas as pd, numpy as np
pd.set_option('display.width',300); pd.set_option('display.max_rows',300)
df = pd.read_pickle('analysis/cfb_clean.pkl'); df=df[(~df.degenerate)&(df.decided==1)].copy()
SH={'ATS':'ATS','Defensive Total':'DefTotal','Turnover and Win Probability':'TurnoverWP','Rithmm AI':'RithmmAI'}
df['M']=df['model'].map(SH); MODELS=['ATS','DefTotal','TurnoverWP','RithmmAI']
print('MODEL vs MARKET SHARPNESS (Brier; lower is better)')
for m in MODELS+['ALL']:
    g=df if m=='ALL' else df[df.M==m]
    y=g['win'].values; p=np.clip(g['Win Probability'].values/100,1e-6,1-1e-6); q=np.clip(g['imp'].values/100,1e-6,1-1e-6)
    print(f'  {m:11s} n={len(g):5d} model={np.mean((p-y)**2):.4f} market={np.mean((q-y)**2):.4f} gap={np.mean((p-y)**2)-np.mean((q-y)**2):+.4f}')
print()
for mk in ['Moneyline','Spread','Total']:
    for m in MODELS:
        g=df[(df.M==m)&(df.market==mk)]
        if len(g)<25: continue
        y=g['win'].values; p=np.clip(g['Win Probability'].values/100,1e-6,1-1e-6); q=np.clip(g['imp'].values/100,1e-6,1-1e-6)
        print(f'  {mk:10s} {m:11s} n={len(g):4d} model={np.mean((p-y)**2):.4f} market={np.mean((q-y)**2):.4f} gap={np.mean((p-y)**2)-np.mean((q-y)**2):+.4f}')
    print()
print('CALIBRATION BY DECILE (all models pooled)')
df['d']=pd.qcut(df['Win Probability'],10,duplicates='drop')
print(df.groupby('d',observed=True).apply(lambda x: pd.Series(dict(n=len(x),
  pred=round(x['Win Probability'].mean(),1), mkt=round(x['imp'].mean(),1),
  actual=round(x['win'].mean()*100,1), err=round(x['win'].mean()*100-x['Win Probability'].mean(),1),
  ROI=round(x['units'].mean()*100,2))), include_groups=False).to_string())
print()
print('PER-MODEL x MARKET x RECOMMENDED, for the playbook')
d2=pd.read_pickle('analysis/cfb_clean.pkl'); d2=d2[~d2.degenerate]; d2['M']=d2['model'].map(SH)
sub=d2[d2.market=='Total']
print('OVERS on lines under 50, by model:')
print(sub[(sub.ou=='Over')&(sub['Totals Value']<50)].groupby('M').apply(lambda x: pd.Series(dict(
  n=len(x),W=int(x.win.sum()),L=int(x.decided.sum()-x.win.sum()),
  WR=round(x.win.sum()/x.decided.sum()*100,1),U=round(x.units.sum(),2),ROI=round(x.units.mean()*100,2))),include_groups=False).to_string())
print()
print('Totals line distribution by O/U pick:')
print(sub.groupby([pd.cut(sub['Totals Value'],[0,45,50,55,60,65,99]),'ou'],observed=True).size().to_string())
