# Simulated Incident: Retry Loop and Budget Exhaustion

## Summary

This is a hypothetical incident, not an observed production outage.

An agent generated an invalid customer lookup parameter. The tool rejected
the request, but the agent repeatedly called the LLM to repair it.
Unbounded retries exhausted the reasoning budget without producing an offer.

## Impact

The request failed, latency increased, and unnecessary tokens were consumed.
No retention offer was successfully approved.

## Illustrative timeline

1. A customer retention request starts.
2. An invalid tool argument causes lookup failure.
3. The agent attempts to repair the argument using the LLM.
4. Repeated invalid arguments keep the recovery loop running.
5. Budget monitoring detects exhaustion and execution is stopped.

This timeline is illustrative; it is not an actual execution log.

## Five Whys

1. Why was the budget exhausted?
   Repeated LLM repair calls consumed tokens without making progress.

2. Why were repair calls needed?
   The agent supplied invalid customer lookup arguments.

3. Why did retries continue?
   Tool failures were treated as indefinitely retryable.

4. Why was the loop not stopped earlier?
   The hypothetical implementation lacked bounded retries, a step limit,
   and pre-call cost reservation.

5. Why were those controls missing?
   Acceptance testing focused on successful requests rather than failure
   recovery and resource limits.

## Root cause

Unbounded recovery logic allowed a tool validation failure to escalate
into excessive token consumption.

## Controls implemented in this project

- Customer lookup requires exactly one matching record.
- The current workflow makes one LLM strategy call without a repair loop.
- RunBudget reserves estimated maximum call cost before execution.
- Lower-risk customers have a $0.05 budget.
- The global hard ceiling is $0.15 per run.
- The SLA middleware enforces a maximum of five admitted steps.
- Circuit breaker OPEN blocks further calls and triggers a Slack alert.
- Output guardrails validate PII and retention policy before approval.

## Verification

SLA self-checks passed for pre-call budget rejection, blocking after OPEN,
a single alert callback event, the step limit, and the global budget ceiling.
Slack notification delivery was verified separately.

The hypothetical retry-loop incident was not replayed end-to-end.

## Follow-up

Before adding an autonomous repair loop, add an integrated regression test
with repeated invalid tool arguments. Verify bounded steps and costs,
circuit breaker activation, and absence of an approved offer.
