*** Settings ***
Library    Collections
Library    RequestsLibrary

*** Test Cases ***
Basic Sanity Check
    ${list}=    Create List    1    2    3

    List Should Contain Value    ${list}    2
    Length Should Be    ${list}    3

Basic Sanity Check 2
    ${a}    Set Variable    4
    ${b}    Set Variable    2

    Should Be True    ${a} + ${b}    6

Basic Sanity Check 4
    ${file}
    
Basic Sanity Check 5
    GET    http://www.msftconnecttest.com/connecttest.txt    expected_status=200