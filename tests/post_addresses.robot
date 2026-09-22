*** Settings ***
Documentation     Tests for POST /addresses on the Customer DB AUT.
...               Requires the AUT to be running at ${BASE_URL} (see AUT/README.md).
Resource          resources/api.resource
Suite Setup       Login As Admin And User
Test Setup        Reset Database    ${ADMIN_TOKEN}
Suite Teardown    Delete All Sessions

*** Variables ***
${ADDRESSES_ENDPOINT}    /addresses

*** Test Cases ***
POST Address Without Token Should Be Unauthorized
    [Documentation]    Creating an address requires authentication.
    &{payload}=    Create Dictionary
    ...    street=1 Test St    city=Testville    zip_code=00-000    country=Testland
    POST On Session    ${SESSION}    ${ADDRESSES_ENDPOINT}    json=&{payload}    expected_status=401
    Address Count Should Be    3

POST Address As Read Only User Should Be Forbidden
    [Documentation]    The read-only "user" account cannot write, per the role rules.
    &{headers}=    Auth Headers    ${USER_TOKEN}
    &{payload}=    Create Dictionary
    ...    street=1 Test St    city=Testville    zip_code=00-000    country=Testland
    POST On Session    ${SESSION}    ${ADDRESSES_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=403
    Address Count Should Be    3

POST Address As Admin Should Create And Persist It
    [Documentation]    Checks the create response, and separately re-fetches the
    ...                resource to confirm it was actually persisted, not just echoed.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    &{payload}=    Create Dictionary
    ...    street=9 New Rd    city=Gdansk    zip_code=80-001    country=Poland
    ${resp}=    POST On Session    ${SESSION}    ${ADDRESSES_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=201
    ${created}=    Set Variable    ${resp.json()}
    Should Be Equal As Strings    ${created}[street]    9 New Rd
    Should Be Equal As Strings    ${created}[city]    Gdansk
    Should Be Equal As Strings    ${created}[zip_code]    80-001
    Should Be Equal As Strings    ${created}[country]    Poland
    Should Be Equal As Integers    ${created}[id]    4

    ${get_resp}=    GET On Session    ${SESSION}    ${ADDRESSES_ENDPOINT}/${created}[id]
    ...    headers=&{headers}    expected_status=200
    Should Be Equal As Strings    ${get_resp.json()}[street]    9 New Rd
    Address Count Should Be    4

POST Address As Admin Missing Required Field Should Be Rejected
    [Documentation]    Omitting "country" should fail schema validation (422),
    ...                and must not create a partial record.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    &{payload}=    Create Dictionary
    ...    street=1 Test St    city=Testville    zip_code=00-000
    POST On Session    ${SESSION}    ${ADDRESSES_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=422
    Address Count Should Be    3

POST Address As Admin With Empty Street Is Currently Accepted
    [Documentation]    Documents present behavior: the AUT does not yet reject empty
    ...                field values. If validation is added later, update this test
    ...                to expect 422 instead of 201.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    &{payload}=    Create Dictionary
    ...    street=${EMPTY}    city=Testville    zip_code=00-000    country=Testland
    ${resp}=    POST On Session    ${SESSION}    ${ADDRESSES_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=201
    Should Be Equal As Strings    ${resp.json()}[street]    ${EMPTY}

*** Keywords ***
Address Count Should Be
    [Arguments]    ${expected_count}
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    ${resp}=    GET On Session    ${SESSION}    ${ADDRESSES_ENDPOINT}    headers=&{headers}    expected_status=200
    Length Should Be    ${resp.json()}    ${expected_count}
