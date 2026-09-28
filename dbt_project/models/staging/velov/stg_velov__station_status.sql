with source as (

    select * from {{ source('velov', 'raw_station_status') }}

),

renamed as (

    select
        station_id,
        ingested_at,
        to_timestamp(last_reported) as last_reported_at,

        num_bikes_available as bikes_available,
        coalesce(
            list_filter(vehicle_types_available, v -> v.vehicle_type_id = 'mechanical')[1]['count'], 0
        ) as mechanical_bikes_available,
        coalesce(
            list_filter(vehicle_types_available, v -> v.vehicle_type_id = 'electrical')[1]['count'], 0
        ) as electric_bikes_available,
        num_bikes_disabled as bikes_disabled,

        num_docks_available as docks_available,
        num_docks_disabled as docks_disabled,

        is_installed,
        is_renting,
        is_returning

    from source

)

select * from renamed