pomodoro
========

# Installation

### Secret key
1. Generate a key with os.urandom(24)
2. Replace "SECRET_KEY='SECRET_KEY'" in the configuration for web.py and server.py

### Create user in database manually
1. Add entry for username and password (TODO: User management)

### Run with Python or Gunicorn
* python server.py (or web.py)
* gunicorn -w 4 -b 0:0:0:0:{port} server:app (or web:app)

# Server API

**PUSH /login** with **user={username}, pass={password}** - Creates session with cookie.

**PUSH /logout** - Ends session

**GET /start?time={timestamp}[&type={type}]** - Starts pomodoro at time (with optional type), returns pomodoroID

**PUSH /end** with **id={pomodoroID}, time={timestamp}** - Ends pomodoro at time
