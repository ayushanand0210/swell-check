# Swell Check — Mulki · Udupi

**Live site: https://ayushanand0210.github.io/swell-check/**

📱 **Add to home screen:** open the URL on your phone → Share → "Add to
Home Screen" — it installs like an app (icon, full screen, always-live data).

One-file web app showing the live 7-day surf outlook for the coastal
Karnataka spots: Sasihitlu/Hejamadi, Padubidri, Malpe, and Kodi Bengre.
No backend, no API key, no cost — the browser fetches Open-Meteo directly
every time the page opens.

## What you're looking at

- **Spot tabs** — one tab per spot; the dot is the week's best rating.
  Your last-viewed spot is remembered on the device.
- **Today block** — big number = today's max swell, plus period, direction,
  and the 6–10 AM wind. Arrows point where the swell/wind is heading.
- **Wave-profile strip** — the week at a glance; dot colour = day rating,
  dashed lines mark the GO (1.2 m) and OK (0.8 m) thresholds.
- **GO** 🟢 = swell ≥ 1.2 m at ≥ 12 s from the SW window (180–280°), with a
  calm or offshore morning (wind read 6–10 AM IST; coast faces west, so
  E/NE is offshore). **OK** = rideable (≥ 0.8 m in window). **SMALL** = nope.
- **today · hour by hour** — tap it on any tab for hourly swell bars + wind.
- Sasihitlu and Hejamadi Kodi share one Open-Meteo grid cell, so they share
  one tab (one forecast, both names).

## Tuning

All knobs are at the top of the `<script>` block in `index.html`:

- `SPOTS` — add beaches as `{ name, lat, lon }` (Varkala: 8.733, 76.703).
  Coordinates are nudged ~1 km offshore on purpose so the marine model
  reads an ocean cell, not land.
- `GO_H = 1.2`, `GO_P = 12` — the "proper day" thresholds
- `OK_H = 0.8` — rideable floor
- `DIR = [180, 280]` — accepted swell direction window (degrees)

Run the scoring sanity check with `node tests/score.test.mjs`.

## Sunday Telegram alert (optional)

`.github/workflows/sunday.yml` sends a forecast snippet to Telegram every
Sunday 7 AM IST via `surf_alert.py`. It does nothing until you add two
repo secrets (Settings → Secrets and variables → Actions):
`TELEGRAM_BOT_TOKEN` (from @BotFather) and `TELEGRAM_CHAT_ID`
(from @userinfobot). Without them the job skips silently.

## Honest limits

Open-Meteo runs global wave models (~5 km grid). It's reliable for swell
arrival timing, size, and period — it does not know the sandbar or exact
nearshore breaking height. GO = "check it", not gospel. Days 6–7 are
directional hints — recheck Thursday.
