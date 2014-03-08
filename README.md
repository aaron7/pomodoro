pomorodo
========

# Server API

**PUSH /login** with **user={username}, pass={password}** - Creates session with cookie.

**PUSH /logout** - Ends session

**GET /start?time=<timestamp>** - Starts pomodoro at time, returns pomodoroID

**PUSH /end** with **id={pomodoroID}, time={timestamp}** - Ends pomodoro at time
