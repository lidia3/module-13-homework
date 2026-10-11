from sla import RunBudget, SLAStop
from slack_alerts import send_open_alert

budget = RunBudget("0.05", on_open=send_open_alert)

try:
    budget.reserve("0.06")
except SLAStop as exc:
    assert budget.state == "OPEN"
    assert budget.steps == 0
    print("EXPECTED HARD STOP:", exc)
else:
    raise AssertionError("Over-budget call was allowed.")

print("SLACK CIRCUIT BREAKER CHECK PASSED")
