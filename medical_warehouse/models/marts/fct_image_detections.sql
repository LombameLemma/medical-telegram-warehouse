{{
    config(
        materialized='table'
    )
}}

/*
Fact table for image detections from YOLO.
Integrates object detection results with message data.
*/

-- First, we need to create a seed or external table for YOLO results
-- For now, we'll assume the CSV has been loaded to raw.yolo_detections

WITH yolo_results AS (
    SELECT
        CAST(message_id AS BIGINT) AS message_id,
        channel_name,
        image_path,
        image_category,
        detected_classes,
        num_detections,
        avg_confidence
    FROM {{ source('raw', 'yolo_detections') }}
),

messages AS (
    SELECT
        message_id,
        channel_key,
        date_key,
        channel_username,
        message_date,
        views,
        forwards
    FROM {{ ref('fct_messages') }}
    WHERE has_image = TRUE
),

image_detections AS (
    SELECT
        m.message_id,
        m.channel_key,
        m.date_key,
        m.channel_username,
        m.message_date,
        y.image_path,
        y.image_category,
        y.detected_classes,
        y.num_detections,
        y.avg_confidence,
        m.views,
        m.forwards,
        
        -- Calculated metrics
        CASE 
            WHEN y.num_detections > 0 THEN TRUE
            ELSE FALSE
        END AS has_objects_detected,
        
        -- Engagement analysis by image type
        m.views AS image_views,
        m.forwards AS image_forwards,
        
        CURRENT_TIMESTAMP AS created_at
    FROM messages m
    INNER JOIN yolo_results y
        ON m.message_id = y.message_id
)

SELECT * FROM image_detections
