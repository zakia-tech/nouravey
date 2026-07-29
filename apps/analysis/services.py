from google import genai
from google.genai import types
from django.conf import settings
from django.utils import timezone

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL_NAME = "gemma-4-26b-a4b-it"
VOICE_MODEL_NAME = "gemini-3.6-flash"

CLASSIFY_FUNCTION = {
    "name": "classify_pollution_report",
    "description": (
        "Classify a citizen pollution report submitted with a photo and either a text "
        "description or a voice note. Assess whether the photo matches the report, then "
        "determine if this is a valid air pollution incident."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "is_relevant": {
                "type": "boolean",
                "description": (
                    "True if this submission describes a genuine outdoor air pollution "
                    "incident (smoke, dust, open burning, industrial emissions) AND the "
                    "photo contextually supports it. False if the submission is off-topic "
                    "or the photo shows something completely unrelated (e.g., a bedroom, "
                    "food, a person)."
                ),
            },
            "rejection_reason": {
                "type": "string",
                "description": (
                    "Short, conversational explanation of why this report was rejected. "
                    "Write in the same language as the citizen's submission "
                    "(English or Kiswahili). Only populate when is_relevant is false."
                ),
            },
            "pollution_type": {
                "type": "string",
                "enum": ["smoke", "dust", "burning", "industrial", "unknown"],
                "description": (
                    "The primary pollution type observed. "
                    "'smoke': visible smoke from vehicles, fires, or cooking. "
                    "'dust': airborne dust from roads, construction, or dry land. "
                    "'burning': open burning of waste, crops, or vegetation. "
                    "'industrial': emissions from factories, quarries, or power plants. "
                    "'unknown': pollution is present but type cannot be determined. "
                    "Only populate when is_relevant is true."
                ),
            },
            "severity": {
                "type": "integer",
                "description": (
                    "Severity of the pollution on a 1-5 scale, based on visual and "
                    "contextual evidence. "
                    "1 = faint haze or trace smell, barely noticeable; "
                    "2 = light smoke or dust, limited to immediate area; "
                    "3 = clearly visible smoke or dust, affects a street or block; "
                    "4 = heavy smoke or dust, covers a neighbourhood, potential health risk; "
                    "5 = thick black smoke, active large fire, or industrial blowout — "
                    "immediate danger. Only populate when is_relevant is true."
                ),
            },
            "confidence": {
                "type": "number",
                "description": (
                    "Your confidence in this overall classification, from 0.0 (very uncertain) "
                    "to 1.0 (certain). Reflect genuine uncertainty — do not default to 1.0."
                ),
            },
            "likely_cause": {
                "type": "string",
                "description": (
                    "A one-sentence explanation of the most probable source of this pollution, "
                    "based on the photo and description. Examples: 'Open burning of plastic waste "
                    "near a residential area', 'Diesel truck emissions at a congested junction'. "
                    "Only populate when is_relevant is true."
                ),
            },
            "image_matches_report": {
                "type": "boolean",
                "description": (
                    "True if the photo is contextually consistent with the pollution described — "
                    "it does not have to show the exact incident, but should be plausibly related "
                    "(e.g., a hazy skyline for a smoke report). "
                    "False only if the photo is clearly unrelated to any pollution incident "
                    "(e.g., a selfie, food, indoor scene)."
                ),
            },
            "mismatch_reason": {
                "type": "string",
                "description": (
                    "Short explanation of why the photo does not match, written in the same "
                    "language as the citizen's submission (English or Kiswahili). "
                    "Only populate when image_matches_report is false."
                ),
            },
        },
        "required": ["is_relevant", "confidence", "image_matches_report"],
    },
}

SYSTEM_INSTRUCTION = """You are a pollution report classifier for Nouravey, a citizen air quality platform serving Mombasa, Kenya. Citizens submit a photo together with either a text description or a voice note about a possible pollution incident.

Your only output is a call to classify_pollution_report. Never respond with plain text.

Follow these steps in order:

STEP 1 — ASSESS THE PHOTO
Decide whether the photo is contextually related to any outdoor air pollution incident.
- PASS: The photo shows smoke, haze, dust, fire, industrial emissions, or a scene plausibly connected to such activity (e.g., a smoky skyline, a burning waste pile, a dusty road). A contextually related photo passes even if it does not show the exact incident described.
- FAIL: The photo is clearly unrelated to pollution — for example, a bedroom, food, a close-up portrait, or an indoor scene.

If the photo FAILS, set image_matches_report to false, is_relevant to false, and populate mismatch_reason and rejection_reason in the same language as the citizen's submission (English or Kiswahili).

STEP 2 — CLASSIFY THE POLLUTION REPORT (only if photo passed Step 1)
Evaluate the description or voice note:
- Is it genuinely about outdoor air pollution in or around Mombasa (smoke, dust, open burning, industrial emissions)?
- If yes: set is_relevant to true and populate pollution_type, severity, and likely_cause.
- If no (e.g., water pollution, noise, unrelated complaint): set is_relevant to false and populate rejection_reason in the citizen's language explaining that this platform covers air pollution only.

SEVERITY SCALE (1-5):
1 = Faint haze or trace smell, barely noticeable
2 = Light smoke or dust, confined to immediate area
3 = Clearly visible smoke or dust, affects a street or block
4 = Heavy smoke or dust, covers a neighbourhood — potential health risk
5 = Thick black smoke, active large fire, or industrial blowout — immediate danger

Always set a confidence score between 0.0 and 1.0 that reflects genuine uncertainty."""

NARRATIVE_SYSTEM_INSTRUCTION = """You are writing a hotspot briefing for a municipal environmental officer in Mombasa, Kenya. You will receive aggregated data about a pollution cluster — citizen reports, air quality index readings, and satellite fire detections where available.

Write a short, professional briefing in two parts:

PART 1 — SITUATION (one short paragraph, 2-3 sentences):
Describe what is happening, where, and why it matters. Be direct. If the score is high or satellite detections confirm active burning, use appropriately urgent language. If data is limited (e.g., a single unconfirmed report), reflect that uncertainty honestly rather than overstating the situation.

PART 2 — RECOMMENDED ACTION (one sentence, on its own line after a blank line):
Recommend one specific, implementable action from this list:
- Dispatch a field inspector to verify and document the incident
- Issue a formal compliance notice to the responsible facility or party
- Coordinate with the fire brigade for active burning incidents
- Activate a public AQI health advisory for the affected ward
- Flag for follow-up monitoring if evidence is insufficient for immediate action

Choose the action that best fits the data. Do not recommend more than one action.

FORMAT RULES:
- Write both parts in plain English
- Do not include headers, labels, bullet points, or markdown
- Do not write "Narrative:" or "Recommended Action:" — start each part directly
- Separate the two parts with a single blank line"""

PREDICT_FUNCTION = {
    "name": "predict_hotspot_trend",
    "description": "Forecast whether a pollution hotspot is likely to worsen, stabilize, or improve over the next 24 hours, based on report trends and corroborating evidence.",
    "parameters": {
        "type": "object",
        "properties": {
            "predicted_trend": {
                "type": "string",
                "enum": ["worsening", "stable", "improving", "insufficient_data"],
                "description": "The most likely direction this hotspot will move in over the next 24 hours."
            },
            "confidence": {
                "type": "number",
                "description": "Confidence in this forecast, from 0.0 to 1.0. Use lower values when evidence is sparse or contradictory."
            },
            "rationale": {
                "type": "string",
                "description": "One or two sentences explaining the reasoning behind this forecast, referencing the specific trend signals used."
            }
        },
        "required": ["predicted_trend", "confidence", "rationale"]
    }
}

PREDICT_SYSTEM_INSTRUCTION = """You are a forecasting assistant for Nouravey, a pollution monitoring platform in Mombasa, Kenya.

Given a summary of a pollution hotspot's recent activity, forecast whether it is likely to worsen, remain
stable, or improve over the next 24 hours. Base your forecast on real trend signals provided to you:
- Whether new citizen reports are accelerating, steady, or slowing
- Whether reported severity is increasing or decreasing over time
- Whether satellite thermal detections indicate ongoing, unaddressed burning (a strong worsening signal,
  since untended fires typically persist or spread without intervention)
- Whether the hotspot's status indicates it is already being addressed (in_progress or resolved reports
  are a stabilizing/improving signal)
- Current air quality context

If there is only one report and no corroborating signals, set predicted_trend to 'insufficient_data' with
a low confidence score rather than guessing.

Always call predict_hotspot_trend. Never respond with plain text."""


def _extract_function_call(response, function_name):
    if not response.candidates:
        raise ValueError("No candidates returned")
    for part in response.candidates[0].content.parts:
        if part.function_call is not None and part.function_call.name == function_name:
            return dict(part.function_call.args)
    raise ValueError(f"No valid function call found for {function_name}")


def _build_narrative_prompt(hotspot, reports, sensor_readings, satellite_hotspots):
    report_summaries = "\n".join([
        f"- {r.get_pollution_type_display()} (severity {r.severity}/5): "
        f"{r.likely_cause or r.text_description[:100]}"
        for r in reports
    ])

    sensor_summary = ""
    if sensor_readings.exists():
        latest = sensor_readings.first()
        sensor_summary = f"\nAir quality sensor — latest city-wide AQI: {latest.aqi}"

    satellite_summary = ""
    if satellite_hotspots.exists():
        satellite_summary = (
            f"\nSatellite thermal data: {satellite_hotspots.count()} active fire "
            f"detection(s) within the cluster, confirming ongoing burning."
        )

    data_quality = "sufficient" if reports.count() >= 3 or satellite_hotspots.exists() else "limited"

    return f"""Location: {hotspot.get_ward_display()} ward, Mombasa
Cluster score: {hotspot.score} — severity label: {hotspot.severity_label}
Number of citizen reports: {reports.count()}
Data quality: {data_quality}

Citizen reports:
{report_summaries}
{sensor_summary}
{satellite_summary}

Write the situation paragraph, then the recommended action."""


def classify_report(photo, text_description="", voice_note=None, debug=False):
    """
    Sends a citizen's report evidence for classification.
    Uses Gemini only when a voice note is present.
    Uses Gemma for all other cases.
    """
    try:
        active_model = VOICE_MODEL_NAME if voice_note else MODEL_NAME
        parts = []

        photo.seek(0)
        image_bytes = photo.read()
        parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=photo.content_type or "image/jpeg"
            )
        )

        if voice_note:
            voice_note.seek(0)
            audio_bytes = voice_note.read()
            parts.append(
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=voice_note.content_type or "audio/mpeg"
                )
            )
        elif text_description:
            parts.append(text_description)

        tool = types.Tool(function_declarations=[CLASSIFY_FUNCTION])

        response = client.models.generate_content(
            model=active_model,
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[tool],
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            )
        )

        if debug:
            print("=== RAW PARTS ===")
            for i, part in enumerate(response.candidates[0].content.parts):
                print(f"Part {i}: {part}")
            print("=================")

        args = _extract_function_call(response, "classify_pollution_report")
        is_relevant = bool(args.get("is_relevant", False))
        image_matches = bool(args.get("image_matches_report", True))

        if not image_matches:
            return {
                "is_relevant": False,
                "rejection_reason": args.get("rejection_reason", "Picha hailingani na taarifa ya uchafuzi wa hewa."),
                "pollution_type": "unknown",
                "severity": 0,
                "confidence": float(args.get("confidence", 0.0)),
                "likely_cause": "",
            }

        return {
            "is_relevant": is_relevant,
            "rejection_reason": args.get("rejection_reason", "") if not is_relevant else "",
            "pollution_type": args.get("pollution_type", "unknown") if is_relevant else "unknown",
            "severity": int(args.get("severity", 3)) if is_relevant else 0,
            "confidence": float(args.get("confidence", 0.0)),
            "likely_cause": args.get("likely_cause", "") if is_relevant else "",
        }

    except Exception as e:
        if debug:
            import traceback
            print("=== CLASSIFICATION ERROR ===")
            traceback.print_exc()
            print("============================")
        return {
            "is_relevant": False,
            "rejection_reason": "Automatic classification unavailable. Manual review needed.",
            "pollution_type": "unknown",
            "severity": 0,
            "confidence": 0.0,
            "likely_cause": f"Error: {type(e).__name__}"
        }


def generate_hotspot_narrative(hotspot):
    """
    Generates a narrative and recommended_action for a Hotspot using Gemma.
    """
    try:
        reports = hotspot.reports.all()
        sensor_readings = hotspot.sensor_readings.all()
        satellite_hotspots = hotspot.satellite_hotspots.all()

        prompt = _build_narrative_prompt(hotspot, reports, sensor_readings, satellite_hotspots)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=NARRATIVE_SYSTEM_INSTRUCTION,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            )
        )

        full_text = response.text.strip()

        if "\n\n" in full_text:
            parts = full_text.split("\n\n", 1)
            hotspot.narrative = parts[0].strip()
            hotspot.recommended_action = parts[1].strip()[:255]
        else:
            hotspot.narrative = full_text
            hotspot.recommended_action = "Dispatch team to assess and respond."

    except Exception:
        hotspot.narrative = (
            f"{hotspot.reports.count()} pollution report(s) in {hotspot.get_ward_display()}, "
            f"scored {hotspot.severity_label}. Automatic narrative generation unavailable."
        )
        hotspot.recommended_action = "Manual review recommended."


def predict_hotspot_trend(hotspot):
    """
    Forecasts a Hotspot's likely 24-hour trajectory using Gemma, based on
    report frequency/severity trends, satellite corroboration, and status.

    Sets hotspot.predicted_trend, prediction_confidence, and
    prediction_rationale directly. Does not save — caller must save.
    """
    try:
        reports = list(hotspot.reports.all().order_by('submitted_at'))

        if not reports:
            hotspot.predicted_trend = 'insufficient_data'
            hotspot.prediction_confidence = 0.0
            hotspot.prediction_rationale = 'No reports available for forecasting.'
            return

        now = timezone.now()
        recent_reports = [r for r in reports if (now - r.submitted_at).total_seconds() <= 24 * 3600]
        older_reports = [r for r in reports if r not in recent_reports]

        report_trend = (
            f"{len(recent_reports)} report(s) in the last 24h vs {len(older_reports)} before that"
        )

        severities_over_time = [
            f"{r.submitted_at.strftime('%m-%d %H:%M')}: severity {r.severity}" for r in reports
        ]

        active_statuses = [r.status for r in reports]
        status_summary = f"Report statuses: {', '.join(set(active_statuses))}"

        satellite_note = ""
        if hotspot.satellite_hotspots.exists():
            satellite_note = (
                f"\n{hotspot.satellite_hotspots.count()} active satellite thermal detection(s) "
                f"— fire may still be burning."
            )

        sensor_note = ""
        latest_sensor = hotspot.sensor_readings.first()
        if latest_sensor:
            sensor_note = f"\nCurrent city-wide AQI: {latest_sensor.aqi}"

        prompt = f"""Hotspot in {hotspot.get_ward_display()} ward
Current score: {hotspot.score} ({hotspot.severity_label})
Report trend: {report_trend}
Severity history: {'; '.join(severities_over_time)}
{status_summary}{satellite_note}{sensor_note}

Forecast the 24-hour trend."""

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=PREDICT_SYSTEM_INSTRUCTION,
                tools=[types.Tool(function_declarations=[PREDICT_FUNCTION])],
                thinking_config=types.ThinkingConfig(thinking_level='minimal'),
            )
        )

        args = _extract_function_call(response, 'predict_hotspot_trend')

        hotspot.predicted_trend = args.get('predicted_trend', 'insufficient_data')
        hotspot.prediction_confidence = float(args.get('confidence', 0.0))
        hotspot.prediction_rationale = args.get('rationale', '')

    except Exception:
        hotspot.predicted_trend = 'insufficient_data'
        hotspot.prediction_confidence = 0.0
        hotspot.prediction_rationale = 'Automatic forecasting unavailable for this hotspot.'


def process_report_into_hotspot(report):
    """
    Full post-save pipeline for a newly created Report.
    """
    from apps.geo.services import cluster_report
    from .scorers import score_hotspot

    hotspot = cluster_report(report)
    score_hotspot(hotspot)
    generate_hotspot_narrative(hotspot)
    predict_hotspot_trend(hotspot)
    hotspot.save()

    return hotspot