import pandas as pd, numpy as np, itertools, math
from math import comb
df = pd.read_pickle('./clean.pkl')

def band(v, edges, labels):
    return pd.cut(v, bins=edges, labels=labels, right=False)

# --- bucket definitions ---------------------------------------------------
DTM_E = [-999,-5,0,2,5,10,20,999]
DTM_L = ['DTM < -5','DTM -5..0','DTM 0..2','DTM 2..5','DTM 5..10','DTM 10..20','DTM 20+']
df['b_dtm'] = band(df['dtm'], DTM_E, DTM_L).astype(str)

WP_E = [0,20,30,40,50,52.5,55,57.5,60,65,101]
WP_L = ['WP <20','WP 20-30','WP 30-40','WP 40-50','WP 50-52.5','WP 52.5-55','WP 55-57.5','WP 57.5-60','WP 60-65','WP 65+']
df['b_wp'] = band(df['win probability'], WP_E, WP_L).astype(str)

OD_E = [-9999,-300,-200,-150,-120,-100,100,150,200,300,500,99999]
OD_L = ['ML <= -300','ML -300..-200','ML -200..-150','ML -150..-120','Juice -120..-100','Dog +100..+150','Dog +150..+200','Dog +200..+300','Dog +300..+500','Dog +500+']
# American odds have no values in (-100,100); collapse
def odds_band(a):
    if a <= -300: return 'Odds <= -300'
    if a <= -200: return 'Odds -300..-200'
    if a <= -150: return 'Odds -200..-150'
    if a <= -120: return 'Odds -150..-120'
    if a <  -110: return 'Odds -120..-110'
    if a <= -105: return 'Odds -110..-105'
    if a <    0:  return 'Odds -105..-100'
    if a <= 150:  return 'Odds +100..+150'
    if a <= 200:  return 'Odds +150..+200'
    if a <= 300:  return 'Odds +200..+300'
    if a <= 500:  return 'Odds +300..+500'
    return 'Odds +500 or longer'
df['b_odds'] = df['payout (american)'].apply(odds_band)

def spr_band(v):
    if pd.isna(v): return 'n/a'
    a = abs(v)
    if a <= 2.5: return 'Spread 0-2.5'
    if a <= 4.5: return 'Spread 3-4.5'
    if a <= 6.5: return 'Spread 5-6.5'
    if a <= 9.5: return 'Spread 7-9.5'
    if a <= 13.5: return 'Spread 10-13.5'
    return 'Spread 14+'
df['b_spread'] = df['spread value'].apply(spr_band)

def tot_band(v):
    if pd.isna(v): return 'n/a'
    if v < 215: return 'Total <215'
    if v < 220: return 'Total 215-220'
    if v < 225: return 'Total 220-225'
    if v < 230: return 'Total 225-230'
    if v < 235: return 'Total 230-235'
    if v < 240: return 'Total 235-240'
    return 'Total 240+'
df['b_total'] = df['totals value'].apply(tot_band)

df.to_pickle('./clean2.pkl')

def binom_p(k, n, p):
    # one-sided P(X>=k)
    if n==0: return 1.0
    return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k, n+1))

def summarize(g):
    n=len(g); dec=int(g['decided'].sum()); w=int(g['win'].sum())
    l=dec-w; pu=n-dec
    u=g['units'].sum(); roi=u/n*100 if n else 0
    wr=w/dec*100 if dec else 0
    be=g['breakeven'].mean()
    p=binom_p(w, dec, be/100) if dec else 1.0
    return dict(n=n, w=w, l=l, push=pu, wr=round(wr,1), units=round(u,2),
                roi=round(roi,2), be=round(be,1), edge=round(wr-be,1), p=round(p,4),
                avg_dtm=round(g['dtm'].mean(),1), avg_wp=round(g['win probability'].mean(),1))

rows=[]
MODELS = list(df['model'].unique())+['ALL MODELS']
for model in MODELS:
    d0 = df if model=='ALL MODELS' else df[df['model']==model]
    for market in ['Moneyline','Spread','Total']:
        d1 = d0[d0['market']==market]
        if not len(d1): continue
        sidecol = 'ou' if market=='Total' else 'venue'
        sides = ['ANY'] + sorted(d1[sidecol].unique())
        roles = ['ANY'] if market=='Total' else ['ANY']+sorted(d1['role'].unique())
        flags = ['ANY','Recommended','Caution']
        numcols = {'Moneyline':['b_dtm','b_wp','b_odds','NONE'],
                   'Spread':['b_dtm','b_wp','b_spread','b_odds','NONE'],
                   'Total':['b_dtm','b_wp','b_total','b_odds','NONE']}[market]
        for side in sides:
            d2 = d1 if side=='ANY' else d1[d1[sidecol]==side]
            for rl in roles:
                d3 = d2 if rl=='ANY' else d2[d2['role']==rl]
                for fl in flags:
                    d4 = d3 if fl=='ANY' else d3[d3['flag']==fl]
                    if len(d4)<8: continue
                    for nc in numcols:
                        if nc=='NONE':
                            s=summarize(d4); s.update(model=model, market=market, side=side,
                                role=rl, flag=fl, dim='(all)', bucket='(all)')
                            rows.append(s)
                        else:
                            for bv,g in d4.groupby(nc):
                                if bv=='n/a' or len(g)<8: continue
                                s=summarize(g); s.update(model=model, market=market, side=side,
                                    role=rl, flag=fl, dim=nc, bucket=str(bv))
                                rows.append(s)
R=pd.DataFrame(rows).drop_duplicates()
R.to_pickle('./scan.pkl')
print('slices:',len(R))
