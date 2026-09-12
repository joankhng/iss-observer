"""ISS overhead notifier.

Polls the ISS position every POLL_SECONDS. If the station is within +/-5 degrees of
MY_LAT/MY_LONG and it is dark at that location, sends one email, then waits
COOLDOWN_SECONDS before it can alert again (a pass lasts only a few minutes).

Runs for RUN_SECONDS then exits, so a scheduler can start a fresh copy
(GitHub Actions jobs are capped at 6 hours). Set RUN_SECONDS=0 to run forever.

Environment variables:
  MY_EMAIL      Gmail address (sender and recipient)
  MY_PASSWORD   Gmail *app password* (16 characters, needs 2-step verification on the account)
  MY_LAT        your latitude in decimal degrees, e.g. 1.306077
  MY_LONG       your longitude in decimal degrees, e.g. 103.919894
  RUN_SECONDS   optional, default 21000 (5h50m)
  POLL_SECONDS  optional, default 60
"""

import os
import smtplib
import time
from datetime import datetime, timezone
from email.message import EmailMessage

import requests

MY_EMAIL = os.environ["MY_EMAIL"]
MY_PASSWORD = os.environ["MY_PASSWORD"]
RUN_SECONDS = int(os.environ.get("RUN_SECONDS", "21000"))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "60"))
COOLDOWN_SECONDS = 20 * 60

MY_LAT = float(os.environ["MY_LAT"])
MY_LONG = float(os.environ["MY_LONG"])
BOX_DEGREES = 5


def is_iss_overhead() -> bool:
    response = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
    response.raise_for_status()
    position = response.json()["iss_position"]
    lat = float(position["latitude"])
    lng = float(position["longitude"])
    return (MY_LAT - BOX_DEGREES <= lat <= MY_LAT + BOX_DEGREES
            and MY_LONG - BOX_DEGREES <= lng <= MY_LONG + BOX_DEGREES)


def is_night() -> bool:
    # formatted=0 returns ISO 8601 times in UTC, so compare against UTC now,
    # not the machine's local clock (the server could be anywhere).
    response = requests.get(
        "https://api.sunrise-sunset.org/json",
        params={"lat": MY_LAT, "lng": MY_LONG, "formatted": 0},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json()["results"]
    sunrise = datetime.fromisoformat(results["sunrise"])
    sunset = datetime.fromisoformat(results["sunset"])
    now = datetime.now(timezone.utc)
    # Singapore: sunrise ~23:00 UTC, sunset ~11:00 UTC. Night = after sunset or before sunrise.
    return now >= sunset or now <= sunrise


def send_email() -> None:
    msg = EmailMessage()
    msg["Subject"] = "Look Up! The ISS is above you"
    msg["From"] = MY_EMAIL
    msg["To"] = MY_EMAIL
    msg.set_content("The ISS is passing within 5 degrees of your position right now. Go outside and look up.")
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_PASSWORD)
        connection.send_message(msg)


def main() -> None:
    started = time.time()
    last_alert = 0.0
    print(f"ISS observer started, polling every {POLL_SECONDS}s for {RUN_SECONDS or 'unlimited'}s", flush=True)
    while RUN_SECONDS == 0 or time.time() - started < RUN_SECONDS:
        try:
            overhead = is_iss_overhead()
            if overhead and is_night() and time.time() - last_alert > COOLDOWN_SECONDS:
                send_email()
                last_alert = time.time()
                print(f"{datetime.now(timezone.utc).isoformat()} alert sent", flush=True)
            elif overhead:
                print(f"{datetime.now(timezone.utc).isoformat()} ISS overhead but daylight or cooling down", flush=True)
        except Exception as exc:  # keep the loop alive through API hiccups
            print(f"{datetime.now(timezone.utc).isoformat()} error: {exc}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
