# SI Daily: handoff between the cloud session and the PowerShell session

Dashboard: https://claude.ai/artifact/1MGzSYaPZRpFs3vSTP1aRD

## Who does what
- **PowerShell Claude (local PC):** pulls data that needs the internet or the
  signed-in Sports Insights session. Runs scripts, then commits the output under
  `si_daily/out/` and pushes.
- **Cloud Claude (phone):** edits the page (`si_daily/dashboard/index.html`),
  uploads data files to the dashboard and wires them in.

## Schedule and travel (new, 2026-10-19)
1. `git pull` and check out branch `si-schedule-travel`.
2. Run, using today's games file (the same rows as the dashboard's "Today's
   games" source, with `sport` and `game` like `ANA@NYR`):

       python si_daily/si_schedule.py --games <path to si_games_YYYYMMDD.json>

   or list the matchups directly:

       python si_daily/si_schedule.py --matchups "NFL:WSH@SF,NHL:ANA@NYR,NHL:COL@PHI,NHL:SJS@TOR,NHL:PIT@UTA,MLB:CLE@TB"

   For NHL games, include the goalie Sports Insights lists for each team (and
   its status, e.g. Confirmed / Expected). Either add `away_goalie`,
   `home_goalie`, `away_goalie_status`, `home_goalie_status` to each NHL row of
   the games file, or pass them:

       --goalies "ANA=Lukas Dostal:Confirmed,NYR=Igor Shesterkin:Expected"

   Workload is then measured for that goalie, and a change from the last
   starter is flagged. With no listed goalie it falls back to the last starter.
   Goalies are often confirmed only an hour or two before puck drop, so re-run
   then if Sports Insights updates them.

3. Read the printed flags for anything that looks wrong (for example a "not
   found in ESPN schedule" note, which means a team abbreviation needs adding to
   `ALIASES` in the script).
4. `git add si_daily/out && git commit -m "Schedule data YYYYMMDD" && git push`.
   The cloud session then uploads it and turns on the new page sections.
   (If this session has the Artifact tools, it can instead upload the file to the
   dashboard and create the `datasets/schedule` source itself. If so, leave the
   page to the cloud session so the two don't overwrite each other's edits.)

Data sources: ESPN's public scoreboard feed (site.api.espn.com) for schedules,
results and extra time; the NHL's own feed (api-web.nhle.com) for starting-goalie
workload and exact OT minutes. Pro leagues only (NFL, NHL, NBA, MLB); college
isn't covered yet.

If the NHL feed fails, NHL rows still come out with a note saying goalie and OT
minutes are missing. Check that the goalie names look right. Past starts come from
the NHL's `starter` mark (otherwise the first goalie who played); names are matched
to Sports Insights' by last name and first initial.
