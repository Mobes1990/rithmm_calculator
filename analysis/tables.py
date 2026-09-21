import pandas as pd, numpy as np
from math import comb
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',400)
df = pd.read_pickle('./clean2.pkl')
SHORT={'Terry Rozier Parlays':'Rozier','Big Money$':'BigMoney','Jebron Lames - S/ML':'Jebron'}
df['M']=df['model'].map(SHORT)

def agg(g):
    dec=g['decided'].sum(); w=g['win'].sum()
    return pd.Series(dict(n=len(g), W=int(w), L=int(dec-w), P=int(len(g)-dec),
        WR=round(w/dec*100,1) if dec else 0, BE=round(g['breakeven'].mean(),1),
        U=round(g['units'].sum(),2), ROI=round(g['units'].mean()*100,2)))

def show(title, keys):
    print('='*110); print(title); print('='*110)
    print(df.groupby(keys, observed=True).apply(agg, include_groups=False).to_string())
    print()

show('A. MODEL x MARKET', ['M','market'])
show('B. MODEL x MARKET x RECOMMENDED/CAUTION (DTM>0 vs <=0)', ['M','market','flag'])
show('C. MODEL x MARKET x SIDE (Home/Away | Over/Under)', ['M','market',np.where(df.market=='Total',df.ou,df.venue)])
show('D. MODEL x ML+SPREAD x FAV/DOG', ['M','market','role'])
show('E. MODEL x MARKET x DTM BAND', ['M','market','b_dtm'])
show('F. MODEL x MARKET x WIN PROB BAND', ['M','market','b_wp'])
show('G. MODEL x SPREAD BAND x ROLE', ['M','b_spread','role'])
show('H. MODEL x TOTAL BAND x O/U', ['M','b_total','ou'])
show('I. MODEL x ML ODDS BAND', ['M','b_odds'])
