/*
Custom test to ensure all view counts are non-negative.
This test should return 0 rows to pass.
*/

SELECT
    message_id,
    channel_username,
    views,
    forwards
FROM {{ ref('fct_messages') }}
WHERE views < 0 OR forwards < 0
