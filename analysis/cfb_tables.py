import pandas as pd, numpy as np
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',500)
df = pd.read_pickle('analysis/cfb_clean.pkl')
df = df[~df.degenerate]
SH={'ATS':'ATS','Defensive Total':'DefTotal','Turnover and Win Probability':'TurnoverWP','Rithmm AI':'RithmmAI'}
df['M']=df['model'].map(SH)

def agg(g):
    dec=g['decided'].sum(); w=g['win'].sum()
    return pd.Series(dict(n=len(g), W=int(w), L=int(dec-w), P=int(len(g)-dec),
        WR=round(w/dec*100,1) if dec else 0, BE=round(g['breakeven'].mean(),1),
        U=round(g['units'].sum(),2), ROI=round(g['units'].mean()*100,2)))
def show(t,keys,d=None):
    print('='*112); print(t); print('='*112)
    print((d if d is not None else df).groupby(keys, observed=True).apply(agg, include_groups=False).to_string()); print()

show('A. THE HEADLINE TEST — does the Recommended flag beat the rest?', ['flag'])
show('B. RECOMMENDED vs CAUTION, by market', ['market','flag'])
show('C. RECOMMENDED vs CAUTION, by model', ['M','flag'])
show('D. MODEL x MARKET x RECOMMENDED', ['M','market','flag'])
show('E. MODEL x MARKET x SIDE', ['M','market', np.where(df.market=='Total',df.ou,df.venue)])
show('F. FAVORITE / UNDERDOG (ML + spread)', ['market','role'], df[df.market!='Total'])
show('G. MODEL x FAV/DOG', ['M','market','role'], df[df.market!='Total'])

def band(v,edges,labels): return pd.cut(v,bins=edges,labels=labels,right=False)
df['b_dtm']=band(df['DTM'],[-99,-5,-2,0,1,3,6,10,999],
   ['DTM < -5','DTM -5..-2','DTM -2..0','DTM 0..1','DTM 1..3','DTM 3..6','DTM 6..10','DTM 10+']).astype(str)
show('H. DTM BAND x MARKET', ['market','b_dtm'])
show('I. DTM BAND x RECOMMENDED (spread+total only)', ['b_dtm','flag'], df[df.market!='Moneyline'])

df['b_wp']=band(df['Win Probability'],[0,20,30,40,50,52.5,55,57.5,60,65,101],
   ['WP <20','WP 20-30','WP 30-40','WP 40-50','WP 50-52.5','WP 52.5-55','WP 55-57.5','WP 57.5-60','WP 60-65','WP 65+']).astype(str)
show('J. WIN-PROB BAND x MARKET', ['market','b_wp'])

def ob(a):
    if a<=-300: return 'Odds <= -300'
    if a<=-200: return 'Odds -300..-200'
    if a<=-150: return 'Odds -200..-150'
    if a<=-120: return 'Odds -150..-120'
    if a< -110: return 'Odds -120..-111'
    if a<=-105: return 'Odds -110..-105'
    if a<0:     return 'Odds -104..-100'
    if a<=150:  return 'Odds +100..+150'
    if a<=250:  return 'Odds +150..+250'
    if a<=450:  return 'Odds +250..+450'
    if a<=800:  return 'Odds +450..+800'
    return 'Odds +800 or longer'
df['b_odds']=df['am'].apply(ob)
show('K. ODDS BAND x MARKET', ['market','b_odds'])
df['juice']=np.where(df['am']>=-110,'Paid -110 or better','Paid -111 or worse')
show('L. JUICE TEST (spread + total) — the NBA finding, retested', ['market','juice'], df[df.market!='Moneyline'])
show('L2. JUICE x ROLE (spreads)', ['juice','role'], df[df.market=='Spread'])

def sb(v):
    a=abs(v)
    if a<=3: return 'Line 0-3'
    if a<=7: return 'Line 3.5-7'
    if a<=10.5: return 'Line 7.5-10.5'
    if a<=14: return 'Line 11-14'
    if a<=21: return 'Line 14.5-21'
    return 'Line 21.5+'
s=df[df.market=='Spread'].copy(); s['b_spr']=s['Spread Value'].apply(sb)
show('M. SPREAD LINE BAND x ROLE', ['b_spr','role'], s)

def tb(v):
    if v<45: return 'Total <45'
    if v<50: return 'Total 45-50'
    if v<55: return 'Total 50-55'
    if v<60: return 'Total 55-60'
    if v<65: return 'Total 60-65'
    return 'Total 65+'
t=df[df.market=='Total'].copy(); t['b_tot']=t['Totals Value'].apply(tb)
show('N. TOTAL LINE BAND x OVER/UNDER', ['b_tot','ou'], t)
show('O. OVER/UNDER x MODEL', ['M','ou'], t)
