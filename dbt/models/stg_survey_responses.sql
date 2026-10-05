{{ config(materialized='table') }}

with source as (
    select
        response_id,
        employee_id,
        quarter,
        satisfaction_score,
        sentiment_label,
        comment
    from {{ source('raw', 'survey_responses') }}
),

renamed as (
    select
        response_id,
        employee_id,
        quarter,
        cast(satisfaction_score as integer) as satisfaction_score,
        sentiment_label,
        comment
    from source
)

select * from renamed
