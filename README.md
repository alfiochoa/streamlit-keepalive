# streamlit-keepalive

Free Streamlit Community Cloud apps hibernate after ~12 hours without traffic. This repo visits each app in a real
headless browser every 6 hours (GitHub Actions, free for public repos), wakes any app that already slept, and fails the
run (GitHub emails the owner) if an app shows an error or never loads.

- Edit the app list in `keepalive.py`.
- Run manually: Actions tab -> keep-streamlit-apps-awake -> Run workflow.
- A Monday heartbeat commit stops GitHub from disabling the schedule after 60 inactive days.
- Only visits the owner's own public demo apps.
