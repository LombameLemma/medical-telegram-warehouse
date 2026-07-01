/*
Custom test to ensure message length matches actual text length.
This test should return 0 rows to pass.
*/

SELECT
    message_id,
    channel_username,
    message_length,
    LENGTH(message_text) AS actual_length
FROM {{ ref('fct_messages') }}
WHERE message_length != LENGTH(message_text)
