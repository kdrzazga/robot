*** Settings ***
Documentation     Tests the person service's tax lookup (GET /persons/{id}/tax) with the
...               TaxInformation service replaced by WireMock, which always answers with
...               the tax_id set in ${TAX_STUB_FILE} ("mock_tax_number").
...               Requires the customer DB (run.py) at ${BASE_URL}.
...               WireMock must listen on port 8001, where the person service looks for
...               the tax service, so the real tax service (run_tax.py) must NOT run.
...               By default WireMock is expected to be running already (standalone JAR
...               locally, a service container in CI). Pass --variable START_WIREMOCK:True
...               to have the suite start the JAR itself (needs Java on PATH).
Resource          resources/api.resource
Library           OperatingSystem
Library           Process
Library           WireMockLibrary
Suite Setup       Setup Stubbed Environment
Suite Teardown    Teardown Stubbed Environment
Test Setup        Clear WireMock Request Log

*** Variables ***
${WIREMOCK_JAR}       ${CURDIR}/resources/wiremock-standalone-3.13.2.jar
${WIREMOCK_PORT}      8001
${WIREMOCK_URL}       http://127.0.0.1:${WIREMOCK_PORT}
${TAX_STUB_FILE}      ${CURDIR}/resources/wiremock/mappings/taxes.json
${START_WIREMOCK}     ${FALSE}

*** Test Cases ***
Person Tax Lookup Should Return Data From Tax Service Stub
    [Documentation]    John Smith (id 1) has TAX_ID TAX-1001. The person service asks the
    ...                tax service for it, and WireMock's answer comes back unchanged.
    &{headers}=    Auth Headers    ${USER_TOKEN}
    ${resp}=    GET On Session    ${SESSION}    /persons/1/tax    headers=&{headers}    expected_status=200
    Should Be Equal    ${resp.json()}[tax_id]    ${MOCK_TAX_NUMBER}

    # WireMock was really called, once, with the person's own TAX_ID.
    @{requests}=    Get Requests    /taxes    GET
    Length Should Be    ${requests}    1
    Should Be Equal    ${requests}[0][url]    /taxes?tax_id=TAX-1001

*** Keywords ***
Setup Stubbed Environment
    IF    ${START_WIREMOCK}    Start WireMock
    Connect To WireMock
    Stub Tax Service To Always Return Mock Tax Number
    Login As Admin And User
    Reset Database    ${ADMIN_TOKEN}

Teardown Stubbed Environment
    Delete All Sessions
    IF    ${START_WIREMOCK}    Terminate Process    wiremock

Start WireMock
    [Documentation]    Runs the WireMock JAR in the background and waits until its admin
    ...                API answers. Its log goes to wiremock.log in the output directory.
    Start Process    java    -jar    ${WIREMOCK_JAR}
    ...    --port    ${WIREMOCK_PORT}    --disable-banner
    ...    alias=wiremock    cwd=${OUTPUT DIR}
    ...    stdout=${OUTPUT DIR}/wiremock.log    stderr=STDOUT
    Wait Until Keyword Succeeds    30s    1s    Started WireMock Should Be Up

Started WireMock Should Be Up
    Process Should Be Running    wiremock
    ...    error_message=WireMock exited. Is port ${WIREMOCK_PORT} taken (e.g. by run_tax.py)? See wiremock.log.
    WireMock Admin API Should Answer

Connect To WireMock
    [Documentation]    Waits for WireMock's admin API, then points WireMockLibrary at it.
    Wait Until Keyword Succeeds    30s    1s    WireMock Admin API Should Answer
    Create Mock Session    ${WIREMOCK_URL}

WireMock Admin API Should Answer
    GET    ${WIREMOCK_URL}/__admin/mappings    expected_status=200

Clear WireMock Request Log
    [Documentation]    WireMockLibrary's own "Reset Request Log" calls
    ...                POST /__admin/requests/reset, which WireMock 3.x no longer has (404).
    ...                DELETE /__admin/requests is the current equivalent.
    DELETE    ${WIREMOCK_URL}/__admin/requests    expected_status=200

Stub Tax Service To Always Return Mock Tax Number
    [Documentation]    Registers the mapping from ${TAX_STUB_FILE} (the same file a standalone
    ...                WireMock loads with --root-dir): any GET /taxes, whatever the query
    ...                string, returns one record. Its tax_id becomes \${MOCK_TAX_NUMBER}, so
    ...                the expected value is defined only in the JSON file.
    ${mapping}=    Get File    ${TAX_STUB_FILE}
    Create Mock Mapping With Data    ${mapping}
    ${stub}=    Evaluate    json.loads($mapping)    modules=json
    Set Suite Variable    ${MOCK_TAX_NUMBER}    ${stub}[response][jsonBody][0][tax_id]
