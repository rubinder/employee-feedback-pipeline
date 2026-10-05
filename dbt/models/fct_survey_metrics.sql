{{ config(materialized='table') }}

with survey_data as (
    select
        r.quarter,
        e.team,
        r.satisfaction_score,
        r.sentiment_label,
        r.response_id
    from {{ ref('stg_survey_responses') }} r
    join {{ ref('stg_employees') }} e on r.employee_id = e.employee_id
),

metrics as (
    select
        quarter,
        team,
        count(distinct response_id) as response_count,
        avg(cast(satisfaction_score as float)) as avg_satisfaction_score,
        count(case when sentiment_label = 'positive' then 1 end)::float
            / nullif(count(response_id), 0) as pct_positive_sentiment,
        count(case when sentiment_label = 'neutral' then 1 end)::float
            / nullif(count(response_id), 0) as pct_neutral_sentiment,
        count(case when sentiment_label = 'negative' then 1 end)::float
            / nullif(count(response_id), 0) as pct_negative_sentiment
    from survey_data
    group by quarter, team
)

select * from metrics
