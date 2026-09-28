with availability as (

    select
        *,
        (bikes_available + bikes_disabled + docks_available + docks_disabled) = 0 as is_silent
    from {{ ref('fct_station_availability') }}

),

aggregated as (

    select
        station_id,
        count(*) as n_snapshots,
        min(ingested_at) as first_seen_at,
        max(ingested_at) as last_seen_at,

        count(*) filter (where is_operational) as n_operational_snapshots,
        avg(is_operational::int) as share_snapshots_operational,

        avg((capacity_gap != 0)::int) filter (where is_operational) as share_gap_when_operational,
        avg(is_silent::int) filter (where is_operational) as share_silent_when_operational,
        avg(capacity_gap) filter (where is_operational) as avg_gap_when_operational,
        max(capacity_gap) filter (where is_operational) as max_gap_when_operational,
        count(distinct capacity_gap) filter (where is_operational) as n_distinct_gaps_when_operational

    from availability
    group by station_id

),

latest as (

    select
        station_id,
        is_installed,
        is_renting,
        is_returning,
        is_operational,
        last_reported_at,
        minutes_since_last_report
    from availability
    qualify row_number() over (partition by station_id order by ingested_at desc) = 1

),

final as (

    select
        aggregated.station_id,
        stations.station_name,
        stations.latitude,
        stations.longitude,
        stations.capacity,

        aggregated.n_snapshots,
        aggregated.first_seen_at,
        aggregated.last_seen_at,

        latest.is_installed as latest_is_installed,
        latest.is_renting as latest_is_renting,
        latest.is_returning as latest_is_returning,
        latest.is_operational as latest_is_operational,
        latest.last_reported_at,
        round(latest.minutes_since_last_report / 60.0, 1) as hours_since_last_report,

        aggregated.share_snapshots_operational,
        aggregated.share_gap_when_operational,
        aggregated.share_silent_when_operational,
        aggregated.avg_gap_when_operational,
        aggregated.max_gap_when_operational,
        aggregated.n_distinct_gaps_when_operational,

        case
            when not latest.is_operational
                and latest.minutes_since_last_report >= {{ var('dormant_after_hours') }} * 60
                then 'dormant'
            when not latest.is_operational
                then 'closed_but_reporting'
            when aggregated.share_silent_when_operational >= {{ var('silent_share_threshold') }}
                then 'silent_while_operational'
            when aggregated.n_operational_snapshots >= {{ var('min_snapshots_for_constant_gap') }}
                and aggregated.n_distinct_gaps_when_operational = 1
                and aggregated.max_gap_when_operational != 0
                then 'constant_gap'
            else 'ok'
        end as quality_status

    from aggregated
    left join {{ ref('dim_stations') }} as stations
        on aggregated.station_id = stations.station_id
    left join latest
        on aggregated.station_id = latest.station_id

)

select * from final