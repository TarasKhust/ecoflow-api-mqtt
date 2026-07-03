Prepared a draft PR fix for this issue.

The change adds a derived Stream Microinverter “Solar Input Power” sensor from the already-confirmed `powGetPv` + `powGetPv2` telemetry, then creates an enabled kWh integration sensor from it for generated-energy tracking. It also redacts `mqtt_username`, `mqtt_password`, `certificateAccount`, and `certificatePassword` from diagnostics.

Verification:
- `python -m pytest` could not run because `pytest` is not installed in this environment.
- `python -m unittest discover -s tests -v` passed: 6 tests.

ISSUE_AGENT_OUTCOME: draft-pr
ISSUE_AGENT_LABELS: none
ISSUE_AGENT_CLOSE: false
ISSUE_AGENT_PR_TITLE: Add Stream Microinverter generated energy sensor