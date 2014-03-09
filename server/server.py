import sqlite3
import os
from flask import Flask, request, session, g, abort, render_template
from secret import SECRET_KEY

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'pomodoro.db'),
    DEBUG=False,
    SECRET_KEY=SECRET_KEY
))
app.config.from_envvar('POMODORO_SETTINGS', silent=True)


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


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


@app.route('/login', methods=['POST'])
def login():
    if query_db("select pass from users where user = ?",
                [request.form['user']], one=True)[0] != request.form['pass']:
        return "Incorrect login", 401
    else:
        session['logged_in'] = True
        session['user_id'] = int(query_db("select id from users where user = ?",
                                 [request.form['user']], one=True)[0])
        return "OK", 200


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return "OK", 200


@app.route("/start")
def start():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    db.execute('insert into pomodoros (user_id, start) values (?, ?)',
               [session.get('user_id'), request.args.get('time')])
    new_id = str(query_db('select last_insert_rowid()', one=True)[0])
    db.commit()
    # Return the lastest pomodoro ID
    return new_id


@app.route("/end", methods=['POST'])
def pomodoro_end():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    db.execute('update pomodoros set end = ? where id = ? and user_id = ?',
               [request.form['time'], request.form['id'], session.get('user_id')])
    db.commit()
    return 'OK', 200


@app.route("/")
def info():
    db = get_db()
    cur = db.execute('select id,user_id,start,end from pomodoros order by id asc')
    entries = cur.fetchall()
    return render_template('info.html', entries=entries)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
