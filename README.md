pip install robotframework-browser
rfbrowser init
pip install robotframework-requests

1. Check AUT/README.md -> tun 2 services mentioned there
2. go to folder test and run robot scripts from there
3. Optionally, open UI under AUT/app/frontend/index.html

## CI

`.github/workflows/robot-tests.yml` runs the whole `tests/` suite on every push and pull request:
it starts the customer DB service, runs WireMock as a service container on port 8001 in place of
the tax service, and uploads `results/` (log.html, report.html) as the `robot-results` artifact.
