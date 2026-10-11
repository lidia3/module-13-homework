import os
from uuid import uuid4
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv(".env", override=True)

from langsmith import Client

for name in ("OPENROUTER_API_KEY", "LANGSMITH_API_KEY"):
    value = os.getenv(name, "").strip()
    if not value or value.startswith("your_"):
        raise SystemExit(f"{name}: NOT SET")

# Authentication check only; no model inference.
response = requests.get(
    "https://openrouter.ai/api/v1/key",
    headers={
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"
    },
    timeout=20,
)
if response.status_code != 200:
    raise SystemExit(
        f"OpenRouter authentication failed: HTTP {response.status_code}"
    )
print("OPENROUTER AUTH PASSED")

client = Client()
project = os.environ["LANGSMITH_PROJECT"]
run_id = uuid4()

client.create_run(
    id=run_id,
    name="connection-check",
    run_type="chain",
    project_name=project,
    inputs={"check": "connection"},
    outputs={"status": "passed", "llm_called": False},
    start_time=datetime.now(timezone.utc),
    end_time=datetime.now(timezone.utc),
)
client.flush()

run = client.read_run(run_id)
assert run.name == "connection-check"
print("LANGSMITH TRACE PASSED")
print("Project:", project)
print("Run ID:", run_id)
