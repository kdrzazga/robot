*** Settings ***
Library    Collections

*** Test Cases ***
Basic Sanity Check
    ${list}=    Create List    1    2    3
    List Should Contain Value    ${list}    2
