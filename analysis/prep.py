import pandas as pd, numpy as np, json, math

FILES = [('32529 rozier copy.xlsx','Terry Rozier Parlays'),
         ('32925 big money copy.xlsx','Big Money$'),
         ('32925 Hebron lames copy.xlsx','Jebron Lames - S/ML')]

frames=[]
for f,n in FILES:
    d = pd.read_excel(''+f, sheet_name='in')
    d['model'] = n
    frames.append(d)
df = pd.concat(frames, ignore_index=True)

df = df.dropna(subset=['bet result'])
df['gt'] = pd.to_datetime(df['game time'])
df['gid'] = df['gt'].dt.date.astype(str)+'|'+df['home team']+'|'+df['away team']

# drop exact duplicate rows (same model/game/market/side/line/odds/prob)
key = ['model','gid','bet type','bet','spread value','totals value','payout (american)','win probability']
before=len(df)
df = df.drop_duplicates(subset=key, keep='first').reset_index(drop=True)
print('dropped exact dupes:', before-len(df), '->', len(df))

# ---- derived fields -------------------------------------------------
am = df['payout (american)']
df['dec'] = df['payout (decimal)']
df['implied_pct'] = np.where(am>0, 100/(am+100), -am/(-am+100))*100
df['edge_pts'] = df['win probability'] - df['implied_pct']      # absolute pct-point edge
df['dtm'] = pd.to_numeric(df['dtm'], errors='coerce')            # relative % edge (Rithmm DTM)

res = df['bet result']
df['win'] = (res=='WIN').astype(int)
df['push'] = (res=='PUSH').astype(int)
df['decided'] = (res!='PUSH').astype(int)
df['units'] = np.where(res=='WIN', df['dec']-1, np.where(res=='LOSS', -1.0, 0.0))

MARKET = {'OutcomeMoneylineWin':'Moneyline','OutcomeSpreadWin':'Spread','OutcomeOverWin':'Total'}
df['market'] = df['bet type'].map(MARKET)

# side / venue
df['venue'] = np.where(df['market']=='Total', 'n/a', df['bet'].str.title())   # Home / Away
df['ou']    = np.where(df['market']=='Total', df['bet'].str.title(), 'n/a')   # Over / Under

# favorite vs underdog
def role(r):
    if r['market']=='Moneyline':
        return 'Underdog' if r['payout (american)']>0 else 'Favorite'
    if r['market']=='Spread':
        if r['spread value']>0: return 'Underdog'
        if r['spread value']<0: return 'Favorite'
        return 'Pickem'
    return 'n/a'
df['role'] = df.apply(role, axis=1)

# recommended vs caution: does the model price beat the market price it was offered?
df['flag'] = np.where(df['dtm']>0, 'Recommended', 'Caution')

# break-even % implied by the price actually taken
df['breakeven'] = df['implied_pct']

df['month'] = df['gt'].dt.to_period('M').astype(str)
df['staked'] = df['amount bet']

df.to_pickle('./clean.pkl')

print(df.groupby(['model','market']).agg(n=('win','size'), wins=('win','sum'),
      wr=('win','mean'), roi=('units','mean')).assign(wr=lambda x:(x.wr*100).round(1),
      roi=lambda x:(x.roi*100).round(2)).to_string())
print()
print('overall units:', round(df['units'].sum(),2), 'ROI', round(df['units'].mean()*100,2))
