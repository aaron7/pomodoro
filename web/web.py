import sqlite3
import os
from flask import Flask, g, render_template
from datetime import date, datetime, timedelta
import time
from collections import defaultdict

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '../server/pomodoro.db'),
    DEBUG=False,
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
    columns = ['id', 'user_id', 'start', 'end', 'type_id']
    return [dict(zip(columns, r)) for r in data]


def count_pomodoros_ts_range(user_id, range_min=0, range_max=2147483647,
                             entry_type=1):
    count = query_db('SELECT COUNT(*) FROM pomodoros WHERE user_id = ? and ' +
                     'end > ? and end < ? and (end - start) > ? and ' +
                     'type_id = ?',
                     [user_id, range_min, range_max,
                      app.config['MIN_POMODORO_TIME'],
                      entry_type],
                     one=True)[0]
    return count


def count_pomodoros_date(user_id, date, entry_type=1):
    end_date = date + timedelta(days=1)
    return count_pomodoros_ts_range(
        user_id,
        range_min=int(time.mktime(date.timetuple())),
        range_max=int(time.mktime(end_date.timetuple()))
    )


def project_hours_date(user_id, date):
    count_seconds = 0
    entries = day_entries(user_id, date, date + timedelta(1))
    day = entries[int(time.mktime(date.timetuple()))]
    for entry in day:
        if entry['type_id'] == 2:
            count_seconds += (entry['end'] - entry['start'])
    return count_seconds / (60.0*60.0)


def date_range(start_date, end_date):
    # Remove any time units from date or datetime
    start_date = date(start_date.year, start_date.month, start_date.day)
    end_date = date(end_date.year, end_date.month, end_date.day)
    # Yield date range
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(days=n)


def day_stats(user_id, start_date, end_date):
    ordered_stats = []
    for day in date_range(start_date, end_date):
        ts = int(time.mktime(day.timetuple()))
        ordered_stats.append(
            {'date': ts,
             'pomodoros': count_pomodoros_date(
                 user_id,
                 day),
             'projectHours': project_hours_date(
                 user_id,
                 day)
             })
    return ordered_stats


def get_entries_ts_range(user_id, range_min, range_max):
    entries = query_db('SELECT id, user_id, start, end, type_id ' +
                       'FROM pomodoros ' +
                       'WHERE user_id = ? and end > ? and end < ? and ' +
                       '(end - start) > ? ORDER BY id asc',
                       [user_id,
                        range_min,
                        range_max,
                        app.config['MIN_POMODORO_TIME']
                        ])
    return sqlite2json(entries)


def day_entries(user_id, start_date, end_date):
    data = defaultdict(list)
    entries = get_entries_ts_range(
        user_id,
        int(time.mktime(start_date.timetuple())),
        int(time.mktime(end_date.timetuple())))

    for entry in entries:
        day = int(time.mktime(date.fromtimestamp(entry['end']).timetuple()))
        data[day].append(entry)

    return data


@app.route("/<username>")
def user_stats(username):
    # Select user id based on the parameter
    user_id = query_db("select id from users where user = ?",
                       [username], one=True)
    if not user_id:
        return "The user %s does exist." % username
    else:
        user_id = user_id[0]

    return render_template(
        'user_stats.html',
        username=username,
        day=datetime.today().weekday(),
        day_stats=list(reversed(day_stats(
                           user_id,
                           date.today() - timedelta(14-1),
                           date.today() + timedelta(1)
                           ))),
        day_entries=day_entries(user_id,
                                date.today() - timedelta(7-1),
                                date.today() + timedelta(1)
                                ),
        today=count_pomodoros_date(user_id, date.today())
        )


@app.route("/")
def welcome():
    return "Hello, world!"

if __name__ == "__main__":
    app.run(host='0.0.0.0')
