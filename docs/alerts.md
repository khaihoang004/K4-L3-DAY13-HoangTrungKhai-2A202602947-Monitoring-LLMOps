# Alerts and Runbooks

All three rules are symptom-based and notify `#llmops-alerts` in Slack. Evaluate
the stated condition continuously over its duration and group notifications by
service and alert name. The dashboard gives 60 minutes of context; each alert
uses its own shorter evaluation window and minimum sample count.

<a id="alert-1"></a>

## Alert 1: Chat Latency High

- **Severity:** Critical
- **Condition / duration:** completed chat latency P95 exceeds 2,000 ms for 5 minutes.
- **Owner:** `llmops-on-call`
- **SLO:** `fast_successful_requests` (99.5% under 2 seconds, rolling 28 days).
- **User impact:** chat answers are slow or time out, consuming the latency error budget.
- **Checks:** inspect the latency and TTFT panel; filter `response_sent` logs by time and feature; follow a slow `correlation_id` into the trace and compare retrieval/generation durations.
- **Mitigation:** if retrieval dominates, reduce retrieval timeout or use a bounded fallback; if generation dominates, reduce output/token budget or route to a healthy model. Disable only a confirmed practice incident.
- **Runbook:** this section and the Metrics → Logs → Traces procedure above.

<a id="alert-2"></a>

## Alert 2: Chat Request Error Rate

- **Severity:** Critical
- **Condition / duration:** `request_failed / request_received > 2%` for 5 minutes, with a minimum of 20 requests in the window to avoid paging on tiny samples.
- **Owner:** `api-on-call`
- **User impact:** requests fail rather than returning a usable answer.
- **Checks:** compare failed and total request counts; group `request_failed` by `error_type`; use `correlation_id` to inspect the failing root and child observations.
- **Mitigation:** roll back the last application/config change if failures began after deploy; otherwise restore the failing dependency or temporarily disable the implicated tool path. Preserve sanitized error evidence.
- **Runbook:** this section and the Metrics → Logs → Traces procedure above.

<a id="alert-3"></a>

## Alert 3: Retrieval Success Degradation

- **Severity:** Warning
- **Condition / duration:** `tool_success == true / non-null tool_success < 90%` for 10 minutes, with at least 10 tool observations.
- **Owner:** `retrieval-on-call`
- **User impact:** answers may lose relevant context or fall back to generic responses.
- **Checks:** inspect retrieval-success rate and error breakdown; find `request_failed` records with `tool_name=retrieval`; compare retriever span status and latency with generation in linked traces.
- **Mitigation:** restore the retrieval dependency, reduce query complexity, or enable the bounded fallback; verify success rate recovers before closing the alert.
- **Runbook:** this section and the Metrics → Logs → Traces procedure above.

## Response Procedure

1. **Metrics:** capture panel, value, threshold, and UTC interval.
2. **Logs:** filter that interval; record one sanitized log event and its `correlation_id`.
3. **Traces:** open the matching trace; compare child span duration and status.
4. **Mitigate:** apply the narrowest reversible action and confirm the metric recovers.
5. **Close:** record root cause, action, prevention, and evidence IDs in the incident report.
