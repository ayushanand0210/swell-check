"""Weekly surf alert for Mulki / Udupi (Malpe).

Fetches 7-day marine + wind forecast from Open-Meteo (free, no key),
scores each day against simple go/no-go thresholds, and sends a
Surfline-style snippet to a Telegram chat.

Runs on GitHub Actions every Sunday morning IST. Cost: zero.
"""

import os
import sys
from datetime import datetime

import requests

SPOTS = {
    "Mulki (Sasihitlu)": (13.071, 74.766),
    "Hejamadi Kodi": (13.078, 74.766),
    "Padubidri": (13.131, 74.752),
    "Udupi (Malpe)": (13.361, 74.688),
    "Kodi Bengre": (13.450, 74.685),
}

# Scoring thresholds — tune to taste
GO_HEIGHT_M = 1.2        # swell height for a proper day
GO_PERIOD_S = 12.0       # >= this = groundswell
OK_HEIGHT_M = 0.8        # rideable windswell floor
SW_DIR_RANGE = (180, 280)  # acceptable swell direction window (deg)

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_marine(lat, lon):
    r = requests.get(MARINE_URL, params={
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "wave_height_max",
            "swell_wave_height_max",
            "swell_wave_period_max",
            "swell_wave_direction_dominant",
        ]),
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
    }, timeout=30)
    r.raise_for_status()
    return r.json()["daily"]


def fetch_morning_wind(lat, lon):
    """Hourly wind, reduced to the 6-10am window per day (the session)."""
    r = requests.get(WEATHER_URL, params={
        "latitude": lat,
        "longitude": lon,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
        "wind_speed_unit": "kn",
    }, timeout=30)
    r.raise_for_status()
    h = r.json()["hourly"]
    out = {}
    for t, spd, dirn in zip(h["time"], h["wind_speed_10m"],
                            h["wind_direction_10m"]):
        day, hour = t[:10], int(t[11:13])
        if 6 <= hour <= 10:
            out.setdefault(day, []).append((spd, dirn))
    return {d: (sum(s for s, _ in v) / len(v),
                sum(x for _, x in v) / len(v)) for d, v in out.items()}


def wind_label(speed_kn, direction):
    # Coast faces ~west: E/NE wind (0-130 deg) is offshore
    offshore = direction <= 130 or direction >= 340
    if speed_kn < 6:
        return "light"
    return f"{'offshore' if offshore else 'onshore'} {speed_kn:.0f}kt"


def score_day(swell_h, period, direction, wind_kn, wind_dir):
    in_window = SW_DIR_RANGE[0] <= direction <= SW_DIR_RANGE[1]
    offshore_or_light = wind_kn < 8 or wind_dir <= 130 or wind_dir >= 340
    if swell_h >= GO_HEIGHT_M and period >= GO_PERIOD_S and in_window:
        return ("\U0001F535 GO", "groundswell") if offshore_or_light \
            else ("\U0001F7E1 OK", "swell but windy")
    if swell_h >= OK_HEIGHT_M and in_window:
        return ("\U0001F7E1 OK", "windswell" if period < 10 else "small swell")
    return ("\u26AA SMALL", "near flat")


def compass(deg):
    pts = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW",
           "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return pts[int((deg + 11.25) % 360 // 22.5)]


def build_report():
    lines = ["\U0001F3C4 *Surf week ahead \u2014 "
             f"{datetime.now():%d %b}*", ""]
    for spot, (lat, lon) in SPOTS.items():
        marine = fetch_marine(lat, lon)
        wind = fetch_morning_wind(lat, lon)
        lines.append(f"*{spot}*")
        best = None
        for i, day in enumerate(marine["time"]):
            sw_h = marine["swell_wave_height_max"][i] or 0
            per = marine["swell_wave_period_max"][i] or 0
            dirn = marine["swell_wave_direction_dominant"][i] or 0
            w_kn, w_dir = wind.get(day, (0, 0))
            badge, note = score_day(sw_h, per, dirn, w_kn, w_dir)
            dayname = datetime.strptime(day, "%Y-%m-%d").strftime("%a")
            lines.append(
                f"{badge} {dayname}: {sw_h:.1f}m @ {per:.0f}s "
                f"{compass(dirn)} \u00b7 am wind {wind_label(w_kn, w_dir)}"
                f" \u00b7 {note}")
            if badge.endswith("GO") and best is None:
                best = dayname
        lines.append(f"_Best bet: {best or 'none \u2014 longboard week'}_")
        lines.append("")
    lines.append("_Model: Open-Meteo global wave \u2014 doesn't know the "
                  "sandbar. Recheck Thu._")
    return "\n".join(lines)


def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=30)
    r.raise_for_status()


if __name__ == "__main__":
    report = build_report()
    print(report)
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        send_telegram(report)
    else:
        sys.stderr.write("No TELEGRAM_BOT_TOKEN set; printed only.\n")
