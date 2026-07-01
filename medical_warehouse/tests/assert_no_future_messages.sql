/*
Custom test to ensure no messages have future dates.
This test should return 0 rows to pass.
*/

SELECT
    message_id,
    channel_username,
    message_date,
    CURRENT_TIMESTAMP AS current_time
FROM {{ ref('fct_messages') }}
WHERE message_date > CURRENT_TIMESTAMP
