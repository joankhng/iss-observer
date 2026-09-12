# ISS observer

Emails you when the International Space Station passes within 5 degrees of your position at night. Polls every 60 seconds. Runs on GitHub Actions for free: a scheduled job starts a fresh watcher every 6 hours, each one polls for 5h50m then exits.

## Setup

1. Gmail: turn on 2-step verification, then create an app password (Google Account > Security > App passwords).
2. Repo secrets (Settings > Secrets and variables > Actions):
   - `MY_EMAIL` Gmail address
   - `MY_PASSWORD` the 16-character app password
   - `MY_LAT` latitude, decimal degrees (e.g. `1.306077`)
   - `MY_LONG` longitude, decimal degrees (e.g. `103.919894`)
3. Actions tab > "ISS observer" > Run workflow, once. The 6-hourly schedule takes over.

## Test the email

Set `BOX_DEGREES = 180` temporarily, run the workflow, wait for the email, revert.

## Run elsewhere

Same script works on any always-on box: set the four environment variables and `RUN_SECONDS=0`.
