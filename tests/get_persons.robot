*** Settings ***
Documentation     Tests for GET /persons on the Customer DB AUT.
...               Requires the AUT to be running at ${BASE_URL} (see AUT/README.md).
Resource          resources/api.resource
Suite Setup       Setup Test Environment
Suite Teardown    Delete All Sessions

*** Variables ***
${PERSONS_ENDPOINT}    /persons

*** Test Cases ***
GET Persons Without Token Should Be Unauthorized
    [Documentation]    /persons requires authentication.
    GET On Session    ${SESSION}    ${PERSONS_ENDPOINT}    expected_status=401

GET Persons As Read Only User Should Succeed
    [Documentation]    The read-only "user" account can GET, per the role rules.
    &{headers}=    Auth Headers    ${USER_TOKEN}
    ${resp}=    GET On Session    ${SESSION}    ${PERSONS_ENDPOINT}    headers=&{headers}    expected_status=200
    ${persons}=    Set Variable    ${resp.json()}
    Length Should Be    ${persons}    3

GET Persons As Admin Should Succeed
    [Documentation]    The admin account can GET too, not just write.
    &{headers}=    Auth Headers    ${ADMIN_TOKEN}
    GET On Session    ${SESSION}    ${PERSONS_ENDPOINT}    headers=&{headers}    expected_status=200

GET Persons Should Return Seeded Persons With Nested Address
    [Documentation]    Response shape: each person embeds its full address, not just an id,
    ...                and the seeded dataset (from POST /reset) is present.
    &{headers}=    Auth Headers    ${USER_TOKEN}
    ${resp}=    GET On Session    ${SESSION}    ${PERSONS_ENDPOINT}    headers=&{headers}    expected_status=200
    @{persons}=    Set Variable    ${resp.json()}

    ${names}=    Create List
    FOR    ${person}    IN    @{persons}
        Dictionary Should Contain Key    ${person}    id
        Dictionary Should Contain Key    ${person}    name
        Dictionary Should Contain Key    ${person}    last_name
        Dictionary Should Contain Key    ${person}    address
        Dictionary Should Contain Key    ${person}[address]    city
        Dictionary Should Contain Key    ${person}[address]    country
        Append To List    ${names}    ${person}[name]
    END

    List Should Contain Value    ${names}    John
    List Should Contain Value    ${names}    Anna
    List Should Contain Value    ${names}    Sherlock

*** Keywords ***
Setup Test Environment
    Login As Admin And User
    Reset Database    ${ADMIN_TOKEN}
