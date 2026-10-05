select *
from {{ ref('stg_survey_responses') }}
where satisfaction_score not in (1, 2, 3, 4, 5)
