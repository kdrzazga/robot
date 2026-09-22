*** Settings ***
Documentation     Tests for POST /persons on the Customer DB AUT.
...               Requires the AUT to be running at ${BASE_URL} (see AUT/README.md).
Resource          resources/api.resource
Suite Setup       Login As Admin And User
Test Setup        Reset Database    ${ADMIN_TOKEN}
Suite Teardown    Delete All Sessions

*** Variables ***
${PERSONS_ENDPOINT}    /persons

*** Test Cases ***
POST Person Without Token Should Be Unauthorized
    [Documentation]    Creating a person requires authentication.
    &{payload}=    Create Dictionary    name=Test    last_name=User    address_id=${1}
    POST On Session    ${SESSION}    ${PERSONS_ENDPOINT}    json=&{payload}    expected_status=401
    Person Count Should Be    3

POST Person As Read Only User Should Be Forbidden
    [Documentation]    The read-only "user" account cannot write, per the role rules.
    &{headers}=    Auth Headers    ${USER_TOKEN}
    &{payload}=    Create Dictionary    name=Test    last_name=User    address_id=${1}
    POST On Session    ${SESSION}    ${PERSONS_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=403
    Person Count Should Be    3

POST Person As Admin Should Create And Persist It
    [Documentation]    The create response is the flat Person schema (no nested address),
    ...                unlike GET /persons/{id}. This checks the flat response, then
    ...                re-fetches via GET to confirm it round-trips with the right address.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    &{payload}=    Create Dictionary    name=Test    last_name=User    address_id=${1}
    ${resp}=    POST On Session    ${SESSION}    ${PERSONS_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=201
    ${created}=    Set Variable    ${resp.json()}
    Should Be Equal As Strings    ${created}[name]    Test
    Should Be Equal As Strings    ${created}[last_name]    User
    Should Be Equal As Integers    ${created}[address_id]    1
    Should Be Equal As Integers    ${created}[id]    4
    Dictionary Should Not Contain Key    ${created}    address

    ${get_resp}=    GET On Session    ${SESSION}    ${PERSONS_ENDPOINT}/${created}[id]
    ...    headers=&{headers}    expected_status=200
    ${fetched}=    Set Variable    ${get_resp.json()}
    Should Be Equal As Strings    ${fetched}[name]    Test
    Dictionary Should Contain Key    ${fetched}    address
    Should Be Equal As Integers    ${fetched}[address][id]    1
    Person Count Should Be    4

POST Person As Admin Missing Required Field Should Be Rejected
    [Documentation]    Omitting "last_name" should fail schema validation (422),
    ...                and must not create a partial record.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    &{payload}=    Create Dictionary    name=Test    address_id=${1}
    POST On Session    ${SESSION}    ${PERSONS_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=422
    Person Count Should Be    3

POST Person As Admin With Nonexistent Address Should Be Rejected
    [Documentation]    address_id is checked against real data at request time, not just
    ...                schema validation, so a nonexistent id should be a 400, not 201.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    &{payload}=    Create Dictionary    name=Test    last_name=User    address_id=${999}
    ${resp}=    POST On Session    ${SESSION}    ${PERSONS_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=400
    Should Contain    ${resp.json()}[detail]    does not reference an existing address
    Person Count Should Be    3

POST Person As Admin With Empty Name Is Currently Accepted
    [Documentation]    Documents present behavior: the AUT does not yet reject empty
    ...                field values. If validation is added later, update this test
    ...                to expect 422 instead of 201.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    &{payload}=    Create Dictionary    name=${EMPTY}    last_name=User    address_id=${1}
    ${resp}=    POST On Session    ${SESSION}    ${PERSONS_ENDPOINT}    json=&{payload}
    ...    headers=&{headers}    expected_status=201
    Should Be Equal As Strings    ${resp.json()}[name]    ${EMPTY}

*** Keywords ***
Person Count Should Be
    [Arguments]    ${expected_count}
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    ${resp}=    GET On Session    ${SESSION}    ${PERSONS_ENDPOINT}    headers=&{headers}    expected_status=200
    Length Should Be    ${resp.json()}    ${expected_count}
