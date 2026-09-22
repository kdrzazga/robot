*** Settings ***
Library    RequestsLibrary
Library    Collections

*** Variables ***
${BASE_URL}         http://127.0.0.1:8000
${SESSION}          aut
${ADMIN_USER}       admin
${ADMIN_PASSWORD}   admin
${TEST_USER}        user
${TEST_PASSWORD}    user

*** Keywords ***
Create API Session
    Create Session    ${SESSION}    ${BASE_URL}

Get Auth Token
    [Documentation]    Logs in via POST /token and returns the JWT access token.
    [Arguments]    ${username}    ${password}
    &{form}=    Create Dictionary    username=${username}    password=${password}
    ${resp}=    POST On Session    ${SESSION}    /token    data=&{form}    expected_status=200
    RETURN    ${resp.json()}[access_token]

Auth Headers
    [Documentation]    Builds an Authorization header dictionary for the given token.
    [Arguments]    ${token}
    &{headers}=    Create Dictionary    Authorization=Bearer ${token}
    RETURN    &{headers}

Reset Database
    [Documentation]    Wipes and re-seeds the AUT's in-memory database (admin only).
    [Arguments]    ${admin_token}
    &{headers}=    Auth Headers    ${admin_token}
    POST On Session    ${SESSION}    /reset    headers=&{headers}    expected_status=200

Login As Admin And User
    [Documentation]    Creates the API session and logs in as both the admin and the
    ...                read-only user, exposing ${ADMIN_TOKEN} / ${USER_TOKEN} as suite
    ...                variables so test cases in any suite can reuse them.
    Create API Session
    ${admin_token}=    Get Auth Token    ${ADMIN_USER}    ${ADMIN_PASSWORD}
    Set Suite Variable    ${ADMIN_TOKEN}    ${admin_token}
    ${user_token}=    Get Auth Token    ${TEST_USER}    ${TEST_PASSWORD}
    Set Suite Variable    ${USER_TOKEN}    ${user_token}
