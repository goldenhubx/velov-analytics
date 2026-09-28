with status as (

    select * from {{ ref('stg_velov__station_status') }}

),

information as (

    select * from {{ ref('stg_velov__station_information') }}

),

joined as (

    select
        status.station_id,
        status.ingested_at,
        status.last_reported_at,

        information.station_name,
        information.latitude,
        information.longitude,
        information.capacity,

        status.bikes_available,
        status.mechanical_bikes_available,
        status.electric_bikes_available,
        status.bikes_disabled,
        status.docks_available,
        status.docks_disabled,

        status.is_installed,
        status.is_renting,
        status.is_returning

    from status
    left join information
        on status.station_id = information.station_id
        and status.ingested_at = information.ingested_at

),

enriched as (

    select
        *,
        bikes_available = 0 as is_empty,
        docks_available = 0 as is_full,
        case
            when capacity > 0 then bikes_available::double / capacity
        end as occupancy_rate,
        capacity - (bikes_available + bikes_disabled + docks_available + docks_disabled) as capacity_gap,
        date_diff('minute', last_reported_at, ingested_at) as minutes_since_last_report,
        (is_installed and is_renting and is_returning) as is_operational

    from joined

)

select * from enriched