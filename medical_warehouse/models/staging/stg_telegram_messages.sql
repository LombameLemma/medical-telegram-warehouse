{{
    config(
        materialized='view'
    )
}}

/*
Staging model for Telegram messages.
Cleans and standardizes raw telegram data.
*/

WITH raw_messages AS (
    SELECT 
        message_id,
        channel_name,
        channel_username,
        message_date,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        scraped_at,
        loaded_at
    FROM {{ source('raw', 'telegram_messages') }}
),

cleaned_messages AS (
    SELECT
        -- IDs
        message_id,
        LOWER(TRIM(channel_username)) AS channel_username,
        TRIM(channel_name) AS channel_name,
        
        -- Dates
        CAST(message_date AS TIMESTAMP) AS message_date,
        DATE(message_date) AS message_date_only,
        
        -- Content
        TRIM(COALESCE(message_text, '')) AS message_text,
        LENGTH(TRIM(COALESCE(message_text, ''))) AS message_length,
        
        -- Media
        has_media,
        CASE 
            WHEN has_media THEN TRUE 
            ELSE FALSE 
        END AS has_image,
        image_path,
        
        -- Metrics
        COALESCE(views, 0) AS views,
        COALESCE(forwards, 0) AS forwards,
        
        -- Metadata
        scraped_at,
        loaded_at,
        
        -- Derived fields
        EXTRACT(HOUR FROM message_date) AS message_hour,
        EXTRACT(DOW FROM message_date) AS day_of_week,
        CASE 
            WHEN EXTRACT(DOW FROM message_date) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend
        
    FROM raw_messages
    
    -- Filter out invalid records
    WHERE message_id IS NOT NULL
      AND channel_username IS NOT NULL
      AND message_date IS NOT NULL
      AND message_date <= CURRENT_TIMESTAMP  -- No future dates
      AND views >= 0  -- No negative views
      AND forwards >= 0  -- No negative forwards
)

SELECT * FROM cleaned_messages
