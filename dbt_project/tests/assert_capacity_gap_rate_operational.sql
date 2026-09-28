-- Alerte si plus de 3 % des mesures des dernières 24 h sur stations opérationnelles
-- ont un écart de capacité supérieur à 3. Seuils calibrés sur ~14 h d'historique (provisoires).
{{ config(severity='warn') }}

with recent as (

    select capacity_gap
    from {{ ref('fct_station_availability') }}
    where is_operational
      and ingested_at >= (
          select max(ingested_at) from {{ ref('fct_station_availability') }}
      ) - interval '24 hours'

),

rate as (

    select
        count(*) filter (where capacity_gap > 3)::double / count(*) as share_above_threshold
    from recent

)

select * from rate
where share_above_threshold > 0.03