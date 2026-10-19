# SI Daily: additions to-do list

Dashboard: https://claude.ai/artifact/1MGzSYaPZRpFs3vSTP1aRD

Goal: show every measurable schedule and situational factor that could affect
the result, for both teams in every game on the daily slate. Build it however
works best on this PC. Every number should come from real data, not estimates.

## Sports to cover
- [ ] NFL
- [ ] NHL
- [ ] NBA
- [ ] MLB
- [ ] College football (all FBS)
- [ ] Men's college basketball (all Division I)

## Schedule and rest (every sport)
- [ ] Days of rest since the last game (0 = back-to-back)
- [ ] Back-to-back flag, and back-to-back tomorrow (look-ahead spot)
- [ ] Games played in the last 7 days and the last 14 days
- [ ] Home vs. road split of those games
- [ ] Schedule density: 3 games in 4 nights, 4 in 6 (NHL, NBA, college basketball)
- [ ] Position in the current road trip or homestand (e.g. "road game 4 of 6")
- [ ] Next game: date, opponent and days until it (look-ahead / letdown spots)
- [ ] Last game: date, opponent, result and score
- [ ] Recent form: current win/loss streak and last-5 record

## Travel (every sport)
- [ ] Miles travelled in the last 7 and 14 days, arena to arena
- [ ] Miles travelled into today's game
- [ ] Count NFL and college teams as flying home between road games; NHL, NBA
      and MLB teams hop city to city on road trips
- [ ] Time zones crossed since the last game (east or west)
- [ ] Start time on the team's body clock (e.g. a West Coast team starting at
      4 PM their time in an early Eastern game)
- [ ] Altitude: flag a visiting team playing high up (Denver, Utah, Wyoming,
      Air Force, Colorado, Colorado State, BYU, New Mexico) when its home is lower
- [ ] Neutral-site and international games, located correctly

## Sport-specific
- [ ] NFL / college football: short week (e.g. Thursday after Sunday), coming
      off a bye, extra rest
- [ ] MLB: day game after a night game
- [ ] MLB: extra innings played in the last 7 and 14 days

## Overtime
- [ ] Games that went past regulation in the last 7 and 14 days
- [ ] Exact overtime minutes: NHL (from goal times; a shootout = the full OT),
      NBA and college basketball (5 minutes per OT period)
- [ ] NFL and college football: overtime games count
- [ ] Flag heavy overtime (e.g. 10+ OT minutes in the last week)
- [ ] Flag a team that went to overtime / extras in its last game

## NHL starting goalie workload
- [ ] Use the goalie Sports Insights lists for tonight (and its status:
      Confirmed / Expected) as the starter
- [ ] If Sports Insights lists none, fall back to whoever started the last game
      and label it that way
- [ ] For that goalie: starts in the last 7 and 14 days, consecutive starts,
      shots faced in the last 7 days, and whether he played last night
- [ ] Workload of every goalie who started for the team in the last 14 days
      (starts, shots faced, minutes)
- [ ] Flag a goalie change from the last starter
- [ ] Flag a goalie who started last night, or has 5+ straight starts
- [ ] Re-check close to puck drop, since goalies are often confirmed late

## On the dashboard
- [ ] On each game card: one line per team with rest, games and miles in the
      last 7 days, tonight's goalie (NHL) and its flags, highlighting the flags
- [ ] In each card's expanded details: a "Schedule and travel" table with every
      factor above, away team vs. home team side by side
- [ ] A new section, "Schedule and travel, every team": one row per team
      with rest, games and miles over 7 and 14 days, trip position and flags
- [ ] A short note explaining how rest, miles and spans are counted
- [ ] Flags written in plain words (e.g. "Back-to-back; road game 4 in a row;
      goalie Dostal started last night")

## Daily routine
- [ ] Run it each morning with the Sports Insights pull, for every game on the slate
- [ ] Re-run before NHL games once goalies are confirmed
- [ ] Note any team that couldn't be matched or any data that didn't load,
      rather than leaving it blank without saying why
