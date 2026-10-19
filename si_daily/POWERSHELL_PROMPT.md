# Task for the PowerShell Claude session: SI Daily schedule and travel data

Pull branch `si-schedule-travel` from origin, then follow `si_daily/HANDOFF.md`:

    git fetch origin si-schedule-travel
    git checkout si-schedule-travel

1. Build today's games list from Sports Insights as a JSON file: one row per
   game with `sport` and `game` (away@home, like `ANA@NYR`).
   - NHL: also add each team's listed goalie and status:
     `away_goalie`, `away_goalie_status`, `home_goalie`, `home_goalie_status`.
   - College: sport `NCAAF` or `NCAAB`, team names as Sports Insights shows them.
2. Run:

       python si_daily/si_schedule.py --games <that file>

3. Show the printed flags. Fix any "not found in ESPN schedule" rows by adding
   the abbreviation to `ALIASES` in the script, then run it again.
4. Commit and push:

       git add si_daily/out si_daily/geo_cache.json
       git commit -m "Schedule data <date>"
       git push origin si-schedule-travel

5. Tell the user it is pushed, so the cloud session can load it into the
   SI Daily dashboard (https://claude.ai/artifact/1MGzSYaPZRpFs3vSTP1aRD).
   Don't edit the dashboard page yourself; the cloud session owns the page.
