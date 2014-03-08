pomorodo
========

# Server API

PUSH /login - user=<username>, pass=<password> - Creates session with cookie.

PUSH /logout - Ends session

GET /start?time=<timestamp> - returns pomodoroID - Starts pomodoro at time

PUSH /end - id=<pomodoroID>, time=<timestamp> - Ends pomodoro at time
