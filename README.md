# Telco-Churn Retention Agent — AgentOps

Customer retention agent powered by a pre-trained churn model, OpenRouter,
LangSmith, Guardrails AI, and GitHub Actions.

## Decision flow

Customer lookup → churn prediction → budget check → LLM strategy →
PII and offer validation → final response.

LangSmith traces show execution stages, token usage, cost, and latency.

## Reliability and safety

- Global budget: $0.15 per run.
- High churn risk (>= 0.70): $0.15 budget.
- Lower churn risk: $0.05 budget.
- Maximum estimated call cost is reserved before execution.
- Circuit breaker OPEN blocks further calls and triggers a Slack alert.
- SLA middleware enforces a five-step limit.
- Discounts above 20% are blocked when risk is below 0.70.
- More than three free months or bonuses above $500 require manual review.
- Guardrails AI checks emails, phones, Telco IDs, and supplied identifiers.
- URL validation allows HTTPS hosts www.telekom.com and www.vodafone.com.
- The current workflow does not execute searches.

PII checks cover the listed types; they are not a universal PII detector.

## Local setup

Use Python 3.10:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Populate .env locally. Never commit credentials.

Copy the trusted Topic 08 model and matching dataset to:

- models/churn_model.pkl
- data/telco_customers.csv

The model was verified with scikit-learn 1.7.2.
Model files, customer data, and credentials are excluded from Git.

## Verification

```bash
OTEL_SDK_DISABLED=true python retention_policy.py
OTEL_SDK_DISABLED=true python safety_guards.py
python sla.py
python verify_connections.py
python verify_slack.py
OTEL_SDK_DISABLED=true python agent.py
OTEL_SDK_DISABLED=true python verify_injection.py
OTEL_SDK_DISABLED=true python evaluate.py
```

verify_slack.py deliberately opens the circuit and sends a test alert.

## Golden dataset and CI

Six scenarios cover high-risk retention, cancellation, loyalty,
low-risk contracts, value concerns, and prompt injection.

The gate requires Accuracy >= 90%, Relevance >= 90%, and a passing
prompt-injection scenario. Scores use a rule-based rubric and do not
measure ML predictive accuracy.

GitHub Actions runs policy, PII/domain, and SLA checks.
Pushes to main and manual runs also evaluate real LLM responses using
frozen ML predictions from evals/profiles.json.
CI does not load or test the original ML model.

Required GitHub Actions secrets:

- OPENROUTER_API_KEY
- LANGSMITH_API_KEY

The evaluation report is uploaded as the golden-evaluation artifact.
Live evaluations incur API costs.

## Recorded local results

- Six golden scenarios passed.
- Accuracy: 100%.
- Relevance: 100%.
- Total successful-run cost: $0.00049380.
- Prompt injection did not obtain an unauthorized maximum discount.
- Policy, PII/domain, and SLA checks passed.
- LangSmith tracing and Slack OPEN alerts were verified.

These results describe a recorded local run. LLM outputs may vary.

## Submission

Include the GitHub repository link, POSTMORTEM.md, a successful Actions
run, and a LangSmith dashboard screenshot showing average cost per run
and span latency.
