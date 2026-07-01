{{
    config(
        materialized='table'
    )
}}

/*
Dimension table for Telegram channels.
Contains channel attributes and aggregated metrics.
*/

WITH channel_data AS (
    SELECT
        channel_username,
        channel_name,
        MIN(message_date) AS first_post_date,
        MAX(message_date) AS last_post_date,
        COUNT(*) AS total_posts,
        COUNT(CASE WHEN has_image THEN 1 END) AS posts_with_images,
        AVG(views) AS avg_views,
        AVG(forwards) AS avg_forwards,
        SUM(views) AS total_views,
        SUM(forwards) AS total_forwards
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_username, channel_name
),

channel_classification AS (
    SELECT
        *,
        -- Classify channels based on name/content
        CASE
            WHEN LOWER(channel_name) LIKE '%pharm%' THEN 'Pharmaceutical'
            WHEN LOWER(channel_name) LIKE '%cosmetic%' THEN 'Cosmetics'
            WHEN LOWER(channel_name) LIKE '%med%' THEN 'Medical'
            ELSE 'Other'
        END AS channel_type,
        
        -- Calculate engagement rate
        CASE 
            WHEN total_posts > 0 
            THEN ROUND((posts_with_images::NUMERIC / total_posts::NUMERIC) * 100, 2)
            ELSE 0
        END AS image_usage_percentage
    FROM channel_data
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['channel_username']) }} AS channel_key,
    channel_username,
    channel_name,
    channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    posts_with_images,
    image_usage_percentage,
    ROUND(avg_views, 2) AS avg_views,
    ROUND(avg_forwards, 2) AS avg_forwards,
    total_views,
    total_forwards,
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
FROM channel_classification
