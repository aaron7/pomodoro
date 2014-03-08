import sqlite3
import os
from flask import Flask, request, session, g, abort, render_template
from datetime import datetime
import time
import json
from collections import defaultdict

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '../server/pomodoro.db'),
    DEBUG=False,
    SECRET_KEY='SECRET_KEY',
    MIN_POMODORO_TIME=15*60
))
app.config.from_envvar('POMODORO_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def sqlite2json(data):
    columns = ['id', 'user_id', 'start', 'end']
    return [dict(zip(columns, r)) for r in data]


def today_count(user_id):
    now = datetime.now()
    previous_midnight = datetime(now.year, now.month, now.day)
    start_of_day = int(time.mktime(previous_midnight.timetuple()))
    end_of_day = int(start_of_day + (24*60*60))

    count = query_db('select COUNT(*) from pomodoros where user_id = ? and end > ? and end < ? and (end - start) > ' +
                     str(app.config['MIN_POMODORO_TIME']),
                     [user_id, start_of_day, end_of_day], one=True)[0]

    return count


def yesterday_count(user_id):
    now = datetime.now()
    previous_midnight = datetime(now.year, now.month, now.day)
    end_of_day = int(time.mktime(previous_midnight.timetuple()))
    start_of_day = int(end_of_day - (24*60*60))

    count = query_db('select COUNT(*) from pomodoros where user_id = ? and end > ? and end < ? and (end - start) > ' +
                     str(app.config['MIN_POMODORO_TIME']),
                     [user_id, start_of_day, end_of_day], one=True)[0]

    return count


def last_week(user_id):
    now = datetime.now()
    previous_midnight = datetime(now.year, now.month, now.day)
    end_of_week = int(time.mktime(previous_midnight.timetuple())) + (24*60*60)
    start_of_week = int(end_of_week - (7*24*60*60))

    last_week = query_db('select id,user_id,start,end from pomodoros where user_id = ? and end > ? and end < ? and (end - start) > ' +
                         str(app.config['MIN_POMODORO_TIME']),
                         [user_id, start_of_week, end_of_week])

    last_week = sqlite2json(last_week)

    data = defaultdict(list)
    day = 1
    for pomodoro in last_week:
        end_time = pomodoro['end']
        if not end_time:
            continue  # No end time recorded yet
        while 1:
            if end_time < start_of_week + (day * 24*60*60):
                # In this day
                offset = start_of_week + ((day-1) * 24*60*60)
                pomodoro["start"] = pomodoro["start"] - offset
                pomodoro["end"] = pomodoro["end"] - offset
                data[day-1].append(pomodoro)
                break
            else:
                day += 1

    return data


@app.route("/<username>")
def user_stats(username):
    user_id = query_db("select id from users where user = ?",
                       [username], one=True)
    if not user_id:
        return "The user %s does exist." % username

    user_id = user_id[0]

    db = get_db()
    cur = db.execute('select id,user_id,start,end from pomodoros where user_id = ? order by id asc', [user_id])
    entries = cur.fetchall()

    visual_last_week = last_week(user_id)

    return render_template('user_stats.html', username=username,
        yesterday=yesterday_count(user_id), visual_last_week=visual_last_week,
        today=today_count(user_id), day=datetime.today().weekday(), entries=entries)

@app.route("/")
def welcome():
    return "Hello, world!"

if __name__ == "__main__":
    app.run(host='0.0.0.0')
