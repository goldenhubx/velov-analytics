with source as (

    select * from {{ source('velov', 'raw_station_information') }}

),

renamed as (

    select
        station_id,
        ingested_at,
        name as station_name,
        address as station_address,
        lat as latitude,
        lon as longitude,
        capacity

    from source

)

select * from renamed