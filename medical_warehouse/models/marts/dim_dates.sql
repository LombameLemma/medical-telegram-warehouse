{{
    config(
        materialized='table'
    )
}}

/*
Date dimension table for time-series analysis.
Generates a complete date spine from the earliest to latest message date.
*/

WITH date_spine AS (
    -- Get the date range from messages
    SELECT
        MIN(message_date_only) AS min_date,
        MAX(message_date_only) AS max_date
    FROM {{ ref('stg_telegram_messages') }}
),

date_range AS (
    -- Generate all dates in the range
    SELECT 
        generate_series(
            (SELECT min_date FROM date_spine),
            (SELECT max_date FROM date_spine),
            '1 day'::interval
        )::DATE AS date_day
),

date_attributes AS (
    SELECT
        date_day,
        EXTRACT(YEAR FROM date_day) AS year,
        EXTRACT(MONTH FROM date_day) AS month,
        EXTRACT(DAY FROM date_day) AS day,
        EXTRACT(DOW FROM date_day) AS day_of_week,
        EXTRACT(WEEK FROM date_day) AS week_of_year,
        EXTRACT(QUARTER FROM date_day) AS quarter,
        
        -- Day name
        TO_CHAR(date_day, 'Day') AS day_name,
        TO_CHAR(date_day, 'Dy') AS day_name_short,
        
        -- Month name
        TO_CHAR(date_day, 'Month') AS month_name,
        TO_CHAR(date_day, 'Mon') AS month_name_short,
        
        -- Is weekend
        CASE 
            WHEN EXTRACT(DOW FROM date_day) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend,
        
        -- Is holiday (placeholder - can be expanded)
        FALSE AS is_holiday,
        
        -- Week start/end dates
        DATE_TRUNC('week', date_day)::DATE AS week_start_date,
        (DATE_TRUNC('week', date_day) + INTERVAL '6 days')::DATE AS week_end_date,
        
        -- Month start/end dates
        DATE_TRUNC('month', date_day)::DATE AS month_start_date,
        (DATE_TRUNC('month', date_day) + INTERVAL '1 month' - INTERVAL '1 day')::DATE AS month_end_date,
        
        -- Year start/end dates
        DATE_TRUNC('year', date_day)::DATE AS year_start_date,
        (DATE_TRUNC('year', date_day) + INTERVAL '1 year' - INTERVAL '1 day')::DATE AS year_end_date
        
    FROM date_range
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['date_day']) }} AS date_key,
    date_day AS full_date,
    year,
    quarter,
    month,
    month_name,
    month_name_short,
    week_of_year,
    day,
    day_of_week,
    day_name,
    day_name_short,
    is_weekend,
    is_holiday,
    week_start_date,
    week_end_date,
    month_start_date,
    month_end_date,
    year_start_date,
    year_end_date,
    CURRENT_TIMESTAMP AS created_at
FROM date_attributes
ORDER BY date_day
