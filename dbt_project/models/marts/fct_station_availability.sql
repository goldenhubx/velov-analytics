{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key=['station_id', 'ingested_at']
    )
}}

select * from {{ ref('int_velov__station_availability') }}

{% if is_incremental() %}
where ingested_at > (select max(ingested_at) from {{ this }})
{% endif %}