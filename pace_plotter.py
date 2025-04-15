import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import fastf1
import fastf1.plotting
from fastf1.ergast import Ergast
from datetime import datetime
import os
import pandas as pd
import sys

fastf1.plotting.setup_mpl(mpl_timedelta_support=False, misc_mpl_mods=False,
                          color_scheme='fastf1')

# Latest race info
ergast = Ergast()
schedule = ergast.get_race_schedule(season=datetime.now().year)
print(schedule.columns)
print(schedule.head)
completed = schedule[schedule['fp2Date'] <= pd.to_datetime(datetime.now())]
latest = completed.iloc[-1]

year = latest['season']
round_number = latest['round']
gp_name = latest['raceName']
session_type = 'FP2'

session = fastf1.get_session(year, round_number, session_type)
session.load()
laps = session.laps.pick_quicklaps()
transformed_laps = laps.copy()
transformed_laps["LapTime (s)"] = laps["LapTime"].dt.total_seconds()

team_order = (
    transformed_laps[["Team", "LapTime (s)"]]
    .groupby("Team")
    .median()["LapTime (s)"]
    .sort_values()
    .index
)

team_palette = {team: fastf1.plotting.get_team_color(team, session=session)
                for team in team_order}

fig, ax = plt.subplots(figsize=(15, 10))
sns.boxplot(
    data=transformed_laps,
    x="Team",
    y="LapTime (s)",
    hue="Team",
    order=team_order,
    palette=team_palette,
    whiskerprops=dict(color="white"),
    boxprops=dict(edgecolor="white"),
    medianprops=dict(color="grey"),
    capprops=dict(color="white"),
)

plt.title(f"{year} {gp_name} - {session_type}")
ax.set(xlabel=None)
plt.tight_layout()

filename = f"static/{year}_{gp_name.replace(' ', '_')}_{session_type}.png"
# Create static folder if it doesn't exist
os.makedirs("static", exist_ok=True)

# Save the file with a consistent name (overwrites each time)
filename = f"static/latest_chart.png"
plt.savefig(filename)
