import pandas as pd, numpy as np
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',500)
df = pd.read_pickle('./clean2.pkl').dropna(subset=['win probability'])
SHORT={'Terry Rozier Parlays':'Rozier','Big Money$':'BigMoney','Jebron Lames - S/ML':'Jebron'}
df['M']=df['model'].map(SHORT)

print('### REAL STAKING: rows where amount bet > 0 (actual wagers) vs paper')
df['staked_flag']=np.where(df['amount bet']>0,'STAKED','PAPER')
print(df.groupby(['M','staked_flag']).apply(lambda x: pd.Series(dict(
  n=len(x), WR=round(x['win'].sum()/max(x['decided'].sum(),1)*100,1),
  unitsFlat=round(x['units'].sum(),2), ROIflat=round(x['units'].mean()*100,2),
  wagered=round(x['amount bet'].sum(),2),
  pnl=round((x['units']*x['amount bet']).sum(),2))), include_groups=False).to_string())
print()
d=df[df['amount bet']>0]
print('Actual $ P/L by model/market:')
print(d.groupby(['M','market']).apply(lambda x: pd.Series(dict(n=len(x),
  wagered=round(x['amount bet'].sum(),2), pnl=round((x['units']*x['amount bet']).sum(),2),
  roi=round((x['units']*x['amount bet']).sum()/x['amount bet'].sum()*100,2))), include_groups=False).to_string())
print()
print('TOTAL actual: wagered', round(d['amount bet'].sum(),2), 'pnl', round((d['units']*d['amount bet']).sum(),2))

print()
print('#'*95); print('PER-MODEL PLAYBOOK: slices with n>=25, both time-halves same sign, ROI>=5% or <=-5%'); print('#'*95)
def halves(g):
    cut=g['gt'].median(); a=g[g['gt']<=cut]; b=g[g['gt']>cut]
    return (a['units'].mean()*100 if len(a) else 0, b['units'].mean()*100 if len(b) else 0)

DIMS=[('b_dtm','DTM'),('b_wp','WinProb'),('b_odds','Odds'),('b_spread','SpreadLine'),
      ('b_total','TotalLine'),('role','Fav/Dog'),('venue','Home/Away'),('ou','Over/Under'),('flag','Rec/Caut')]
rows=[]
for m in ['BigMoney','Jebron','Rozier']:
    for mk in ['Moneyline','Spread','Total']:
        base=df[(df.M==m)&(df.market==mk)]
        if len(base)<20: continue
        combos=[('(all)','(all)',base)]
        for dim,dl in DIMS:
            for bv,g in base.groupby(dim):
                if bv in ('n/a','nan') or len(g)<25: continue
                combos.append((dl,str(bv),g))
        # two-way: role x odds-juice, side x role, side x juice
        base2=base.copy(); base2['juice']=np.where(base2['payout (american)']>=-110,'<=-110 juice','-111..-122 juice')
        for k1 in ['role','venue','ou']:
            for k2 in ['juice','flag']:
                for (a,b),g in base2.groupby([k1,k2]):
                    if a in ('n/a','nan') or len(g)<25: continue
                    combos.append((f'{k1} x {k2}', f'{a} + {b}', g))
        for dl,bv,g in combos:
            h1,h2=halves(g); roi=g['units'].mean()*100
            rows.append(dict(model=m, market=mk, dim=dl, bucket=bv, n=len(g),
              W=int(g['win'].sum()), L=int(g['decided'].sum()-g['win'].sum()),
              WR=round(g['win'].sum()/max(g['decided'].sum(),1)*100,1),
              ROI=round(roi,2), U=round(g['units'].sum(),2),
              H1=round(h1,1), H2=round(h2,1), stable=(h1>0)==(h2>0)))
P=pd.DataFrame(rows).drop_duplicates(subset=['model','market','dim','bucket'])
P.to_pickle('./playbook.pkl')
for m in ['BigMoney','Jebron','Rozier']:
    g=P[(P.model==m)&(P.stable)&(P.ROI>=5)].sort_values('ROI',ascending=False)
    print(f'\n@@@ {m} — STABLE WINNERS (both halves positive)'); print(g.head(14).to_string(index=False))
    b=P[(P.model==m)&(P.stable)&(P.ROI<=-5)].sort_values('ROI')
    print(f'@@@ {m} — STABLE LEAKS (both halves negative)'); print(b.head(8).to_string(index=False))
