with ranked as (

    select
        *,
        row_number() over (partition by station_id order by ingested_at desc) as recency_rank
    from {{ ref('stg_velov__station_information') }}

)

select
    station_id,
    station_name,
    station_address,
    latitude,
    longitude,
    capacity,
    ingested_at as last_seen_at
from ranked
where recency_rank = 1