import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)


def send_open_alert(reason: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("SLACK_WEBHOOK_URL is not configured.")

    try:
        response = requests.post(
            webhook,
            json={
                "text": (
                    ":rotating_light: AgentOps Lab 13\n"
                    "Circuit Breaker: CLOSED -> OPEN\n"
                    f"Reason: {reason}\n"
                    "Further LLM calls for this run are blocked."
                )
            },
            timeout=10,
            allow_redirects=False,
        )
    except requests.RequestException:
        # Do not expose the secret webhook URL in error output.
        raise RuntimeError("Slack alert delivery failed: network error.") from None

    if response.status_code != 200 or response.text.strip() != "ok":
        raise RuntimeError(
            f"Slack alert delivery failed: HTTP {response.status_code}"
        )

    print("SLACK ALERT DELIVERED")
