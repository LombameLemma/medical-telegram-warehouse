{{
    config(
        materialized='table'
    )
}}

/*
Fact table for Telegram messages.
Central fact table containing message-level data with foreign keys to dimensions.
*/

WITH messages AS (
    SELECT
        message_id,
        channel_username,
        message_date,
        message_date_only,
        message_text,
        message_length,
        has_media,
        has_image,
        image_path,
        views,
        forwards,
        message_hour,
        day_of_week,
        is_weekend
    FROM {{ ref('stg_telegram_messages') }}
),

enriched_messages AS (
    SELECT
        m.message_id,
        
        -- Foreign keys
        {{ dbt_utils.generate_surrogate_key(['m.channel_username']) }} AS channel_key,
        {{ dbt_utils.generate_surrogate_key(['m.message_date_only']) }} AS date_key,
        
        -- Attributes
        m.channel_username,
        m.message_date,
        m.message_text,
        m.message_length,
        m.has_media,
        m.has_image,
        m.image_path,
        
        -- Metrics
        m.views,
        m.forwards,
        
        -- Derived metrics
        CASE 
            WHEN m.message_length > 0 THEN ROUND(m.views::NUMERIC / m.message_length::NUMERIC, 2)
            ELSE 0
        END AS views_per_character,
        
        CASE
            WHEN m.views > 0 THEN ROUND((m.forwards::NUMERIC / m.views::NUMERIC) * 100, 2)
            ELSE 0
        END AS forward_rate_percentage,
        
        -- Time attributes
        m.message_hour,
        m.day_of_week,
        m.is_weekend,
        
        -- Categorization
        CASE
            WHEN m.message_length = 0 THEN 'Empty'
            WHEN m.message_length < 50 THEN 'Short'
            WHEN m.message_length < 200 THEN 'Medium'
            WHEN m.message_length < 500 THEN 'Long'
            ELSE 'Very Long'
        END AS message_length_category,
        
        CASE
            WHEN m.views < 100 THEN 'Low'
            WHEN m.views < 500 THEN 'Medium'
            WHEN m.views < 1000 THEN 'High'
            ELSE 'Very High'
        END AS engagement_category,
        
        CURRENT_TIMESTAMP AS created_at
    FROM messages m
)

SELECT * FROM enriched_messages
