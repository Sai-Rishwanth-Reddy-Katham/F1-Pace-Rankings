import matplotlib
matplotlib.use('Agg')  # ✅ Prevent Tkinter backend issues

from flask import Flask, render_template, request, redirect, send_file, jsonify
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import fastf1
import fastf1.plotting
from fastf1.ergast import Ergast
import os



app = Flask(__name__)

@app.route('/')
def index():
    image_requested = request.args.get('year') is not None
    return render_template("index.html", image_requested=image_requested)

@app.route('/generate', methods=['POST'])
def generate():
    year = request.form['year']
    gp_name = request.form['gp_name']
    session_type = request.form['session_type']
    return redirect(f"/?year={year}&gp_name={gp_name}&session_type={session_type}")

@app.route('/races/<int:year>')
def get_races(year):
    try:
        ergast = Ergast()
        schedule = ergast.get_race_schedule(year)
        race_names = schedule['raceName'].tolist()
        return jsonify(race_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/plot')
def plot():
    try:
        year = int(request.args.get('year'))
        gp_name = request.args.get('gp_name')
        session_type = request.args.get('session_type')

        session = fastf1.get_session(year, gp_name, session_type)
        session.load(laps=True, telemetry=False, weather=False, messages=False)
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

        fastf1.plotting.setup_mpl(mpl_timedelta_support=False, misc_mpl_mods=False, color_scheme='fastf1')

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

        plt.title(f"{year} {gp_name} - {session_type}", fontsize=20, fontweight='bold', color='white')
        ax.set_facecolor('#1c1c1c')
        fig.patch.set_facecolor('#121212')
        ax.set(xlabel=None)
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return send_file(buf, mimetype='image/png')

    except Exception as e:
        print(f"[ERROR] Failed to generate plot: {e}")
        return f"<h2 style='color:red;'>Error generating plot: {str(e)}</h2>"

# 🏁 Start the app at the very end
if __name__ == '__main__':
    app.run(debug=True)
