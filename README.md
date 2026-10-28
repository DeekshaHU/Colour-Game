# Colour Rush — Full-Stack Colour Recognition Game

A simple Flask + SQLite web app with a clean white website and a soft pink game card. The game block is intentionally a different colour from the page, while the rest of the design stays light and readable.

## Run on Windows (VS Code PowerShell)

1. Extract this ZIP and open the `colour_game_fullstack` folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create an environment: `python -m venv venv`
4. Activate it: `.\venv\Scripts\Activate.ps1`
5. Install dependencies: `python -m pip install -r requirements.txt`
6. Start the app: `python app.py`
7. Open `http://127.0.0.1:5000` in your browser.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again. Alternatively, run `venv\Scripts\python.exe -m pip install -r requirements.txt` and `venv\Scripts\python.exe app.py` without activating.

The SQLite database is created automatically on first run. Keep `venv/` and `colour_game.db` out of Git; `.gitignore` already excludes them.

## Styling

The stylesheet is `static/style.css`. The template loads it using Flask's `url_for('static', filename='style.css', v=3)` to help browsers fetch the updated stylesheet. If the page ever looks unstyled, verify `http://127.0.0.1:5000/static/style.css` loads and then press `Ctrl+Shift+R`.

# Colour Rush — Full-Stack Colour Recognition Game

A full-stack web application built with Python, Flask, SQLite, HTML, CSS, and JavaScript.

## Features
- User registration and login with hashed passwords
- Timed 30-second colour-recognition game
- Randomized word and font-colour challenges
- Score, streak, correct-answer count, and accuracy
- SQLite persistence for game results
- User dashboard and recent game history
- Leaderboard based on each player's best score
- Responsive interface

## Requirements
- Python 3.10 or newer recommended
- pip

## Run locally (Windows)

1. Open a terminal in this project folder.
2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate it:

   ```bash
   venv\\Scripts\\activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the application:

   ```bash
   python app.py
   ```

6. Open http://127.0.0.1:5000 in your browser.
7. Create an account and play.

The SQLite database `colour_game.db` is created automatically in the project folder.

## Important security note
This is a learning/portfolio implementation. The browser submits the final score, so a determined user could tamper with it. For production use, generate challenges and validate answers and timing on the server. Set a strong persistent `SECRET_KEY` in the deployment environment, use HTTPS, add CSRF protection and rate limiting, and review authentication/session settings before publishing.

## Database
- `users`: username, email, password hash, created timestamp
- `game_results`: user, score, correct/total answers, duration, played timestamp

No external dataset is required. Colour challenges are generated randomly by the game.
