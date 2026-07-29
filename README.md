# Nouravey

**A Gemma 4-powered pollution intelligence platform for Mombasa County, Kenya.**

Built for the *Build with Gemma: GDG Pwani Hackathon* — Track 2: CleanAir & Clear Streets.

Nouravey turns scattered citizen pollution reports into structured, prioritized, forward-looking intelligence for municipal environmental officers — combining citizen-submitted photos, text, and voice with live air quality data and satellite fire detection, all reasoned over by Gemma 4.

---

## How Gemma 4 Is Used

Gemma 4 (`gemma-4-26b-a4b-it`) is the reasoning engine behind every stage of the pipeline, called via native function calling (not prompted JSON) for reliable, strictly-typed structured output:

| Function | Location | What it does |
|---|---|---|
| `classify_report()` | `apps/analysis/services.py` | Given a citizen's photo + text/voice, determines if the submission is genuinely about air pollution, checks whether the photo matches the description, and — if valid — extracts `pollution_type`, `severity` (1–5), `confidence`, and `likely_cause`. Responds in the citizen's own language (English or Kiswahili). |
| `generate_hotspot_narrative()` | `apps/analysis/services.py` | Once reports are clustered into a hotspot, synthesizes the aggregated evidence (report count, severity, satellite data, AQI) into a plain-English situation summary and one specific recommended municipal action. |
| `predict_hotspot_trend()` | `apps/analysis/services.py` | Forecasts whether a hotspot is likely to worsen, stabilize, or improve over the next 24 hours, reasoning over report frequency trends, severity trajectory, satellite persistence, and municipal response status. |

Voice submissions route to Gemini (`gemini-3.6-flash`) — classification happens directly on the audio in a single multimodal call, with no separate transcription step.

## Architecture

Django 5.2 modular monolith, six apps:

- **`reports`** — citizen submission intake, serializers, models
- **`sensors`** — IQAir air quality ingestion
- **`satellite`** — NASA FIRMS fire/thermal detection ingestion
- **`analysis`** — all Gemma 4 integration, clustering trigger, scoring, hotspot model
- **`geo`** — proximity-based clustering logic, ward/subcounty boundary data
- **`dashboard`** — map UI, public API endpoints

**Database:** PostgreSQL via Supabase. **Media storage:** Supabase S3-compatible object storage. **Frontend:** Leaflet.js map + a conversational citizen report-submission UI (vanilla JS).

## Data Sources

- **IQAir** — live city-wide Air Quality Index for Mombasa (free tier: city-level granularity only)
- **NASA FIRMS** — near-real-time satellite thermal/fire detection within Mombasa's bounding box

## Running Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) with your own Supabase, Gemini, IQAir, and FIRMS credentials, then:

```bash
python manage.py migrate
python manage.py runserver
```

To populate realistic demo data (clustered reports across multiple wards, with real Gemma-generated narratives and predictions):

```bash
python manage.py seed_demo_data --clear
```

## License

Apache License 2.0