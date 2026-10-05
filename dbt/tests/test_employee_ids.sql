select *
from {{ ref('stg_survey_responses') }}
where employee_id is null
