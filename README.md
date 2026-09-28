## Cas d'étude qualité de données : cohérence des capacités / Data quality case study: capacity consistency

### 🇫🇷 Français

**Le test.** Pour chaque station, la capacité devrait être égale à la somme : vélos disponibles + vélos hors service + bornes libres + bornes hors service. J'ai exprimé cette règle sous la forme d'une colonne `capacity_gap` (capacité moins cette somme, attendue à 0) et d'un test dbt.

**Ce que le test a révélé.** Sur 26 970 mesures (465 stations × 58 snapshots, environ 14 h), 23 % présentent un écart non nul, et 420 stations sur 465 sont concernées à un moment donné. Une lecture par état de la station distingue trois populations :

| Population | Lignes avec écart | Écart moyen |
|---|---|---|
| Station active (installée, location et retour ouverts) | 5 795 | 1,8 |
| Station non installée (aucun rapport depuis plus d'un an) | 290 | 16 |
| Installée, location fermée, retour ouvert | 234 | 21 |

Les écarts des stations actives sont petits (+1 à +3 pour l'essentiel). Ceux des deux autres populations sont grands et constants : pour les stations mortes, tous les compteurs sont à zéro, donc l'écart est la capacité elle-même. Trois mesures sont par ailleurs au-dessus de la capacité (écart de -1), ce qui ne devrait pas arriver.

**Ce que la calibration a montré.** Sur les stations opérationnelles, l'écart médian est de 0, le 95e percentile de 2 et le 99e de 5 (maximum 19), et 1,5 % des mesures ont un écart supérieur à 3. Pour la grande majorité des stations, l'écart varie d'un snapshot à l'autre : ce n'est donc pas, en général, une capacité de référence obsolète mais un phénomène dynamique, cohérent avec l'hypothèse d'un décalage entre compteurs (ou de vélos en cours de verrouillage), qui n'est pas vérifiée à ce stade. Une minorité de stations (47) a un écart constant : 42 sont toujours à 0, 5 ont un écart constant non nul et méritent une investigation. Les trois seules mesures au-dessus de la capacité (écart de -1) concernent trois stations différentes, chacune sur un seul snapshot : du bruit ponctuel, pas un changement durable de capacité.
Cinq stations ont un écart constant non nul : quatre de faible amplitude (+1 à +3), et une station déclarée opérationnelle dont tous les compteurs sont à zéro (écart égal à la capacité), donc active sur le papier mais muette en pratique.

**Décisions.**
- Une tolérance d'une unité sous la capacité (écart supérieur ou égal à -1), sur toutes les lignes : les lectures des compteurs ne semblent pas parfaitement simultanées, donc un -1 isolé n'est pas alarmant, alors qu'un écart plus négatif le serait.
- Un test de taux plutôt qu'un compte absolu : alerte si plus de 3 % des mesures des dernières 24 h sur stations opérationnelles (`is_operational`) ont un écart supérieur à 3. Un compte absolu sur une table qui grossit aurait alerté en permanence.
- Les tests sont en `warn` : un écart est une information sur la donnée, pas une panne du pipeline.
- Les seuils (tolérance de -1, écart > 3, taux de 3 %) sont provisoires, calibrés sur un historique court, et seront réévalués quand celui-ci aura grossi.

**Décisions.**
- Un test « jamais au-dessus de la capacité », qui exprime un invariant physique, sur toutes les lignes.
- Un test de taux plutôt qu'un compte absolu : alerte si plus de 3 % des mesures des dernières 24 h sur stations opérationnelles (`is_operational`) ont un écart supérieur à 3. Un compte absolu sur une table qui grossit aurait alerté en permanence.
- Les tests sont en `warn` : un écart est une information sur la donnée, pas une panne du pipeline.
- Les seuils (écart > 3, taux de 3 %) sont provisoires, calibrés sur environ 14 h d'historique, et seront réévalués quand l'historique aura grossi.

**Ce que ça illustre.** Un test qui échoue ne signifie pas forcément qu'il faut « réparer » la donnée : ici il a servi de détecteur pour comprendre comment le système source se comporte, et pour affiner la définition de ce qu'on considère comme une anomalie.

### 🇫🇷 Profil qualité par station

Un mart `mart_station_quality` classe chaque station selon son historique. Au 28/09/2026 (465 stations) : 448 `ok`, 4 à écart de capacité constant, 1 station déclarée opérationnelle mais muette (tous compteurs à zéro), 9 stations dormantes (silence de plus de 7 jours) et 3 stations fermées mais qui rapportent encore. La séparation entre « dormante » et « fermée mais rapportant » vient d'un premier découpage jugé trop grossier : le statut initial regroupait des situations différentes. Un test a aussi montré que `not_null` ne suffit pas : une station avait un nom vide, ce que seul un test dédié détecte. Les seuils sont des variables dbt provisoires.

**Vérification externe.** J'ai recoupé trois stations avec l'application officielle : deux sont fermées pour travaux (réouverture annoncée en octobre 2026), ce qui correspond à leur statut `closed_but_reporting` ; la troisième, sans nom dans le flux (le test de nom vide l'a signalée), est fermée jusqu'à fin 2026 et apparaît comme `dormant`. « Dormant » recouvre donc aussi des fermetures temporaires, et l'API ne fournit ni motif ni date de réouverture : la classification décrit le comportement du flux, pas sa cause. Trois stations choisies à la main sont cohérentes avec la classification mais ne constituent pas une validation statistique. Par ailleurs, `last_reported` ne semble pas un indicateur de vivacité fiable pour une station saine (médiane de 6 h, maximum de 8,8 h chez les stations `ok`), ce qui rend le seuil de dormance (7 jours) peu sensible.

### 🇬🇧 English

**The test.** For each station, capacity should equal the sum of available bikes, disabled bikes, available docks and disabled docks. I encoded this rule as a `capacity_gap` column (capacity minus that sum, expected to be 0) and a dbt test.

**What the test revealed.** Across 26,970 measurements (465 stations × 58 snapshots, about 14 hours), 23% show a non-zero gap, and 420 of 465 stations are affected at some point. Breaking it down by station state shows three populations:

| Population | Rows with a gap | Average gap |
|---|---|---|
| Active station (installed, renting and returning enabled) | 5,795 | 1.8 |
| Not installed (no report for over a year) | 290 | 16 |
| Installed, renting disabled, returning enabled | 234 | 21 |

Gaps on active stations are small (mostly +1 to +3). The other two populations show large, constant gaps: for dead stations every counter is zero, so the gap is simply the capacity. Three measurements also exceed capacity (gap of -1), which should not happen.

**What calibration showed.** On operational stations, the median gap is 0, the 95th percentile is 2 and the 99th is 5 (maximum 19), and 1.5% of measurements show a gap above 3. For the vast majority of stations the gap varies from one snapshot to the next: it is therefore generally not a stale reference capacity but a dynamic phenomenon, consistent with the hypothesis of counter timing differences (or bikes mid-lock), which is not verified at this stage. A minority of stations (47) show a constant gap: 42 are always at 0, while 5 have a constant non-zero gap and deserve investigation. The only three measurements above capacity (gap of -1) belong to three different stations, each on a single snapshot: isolated noise, not a lasting capacity change.
Five stations show a constant non-zero gap: four of small amplitude (+1 to +3), and one station declared operational whose counters are all zero (gap equal to capacity), so active on paper but silent in practice.

**Decisions.**
- A tolerance of one unit below capacity (gap greater than or equal to -1), on all rows: counter reads do not appear perfectly simultaneous, so an isolated -1 is not alarming, whereas a more negative gap would be.
- A rate test rather than an absolute count: alert if more than 3% of the last 24 hours of measurements on operational stations (`is_operational`) show a gap above 3. An absolute count on a growing table would warn forever.
- Tests use `warn`: a gap is information about the data, not a pipeline failure.
- Thresholds (-1 tolerance, gap > 3, 3% rate) are provisional, calibrated on a short history, and will be revisited as it grows.

**Decisions.**
- A "never above capacity" test, expressing a physical invariant, on all rows.
- A rate test rather than an absolute count: alert if more than 3% of the last 24 hours of measurements on operational stations (`is_operational`) show a gap above 3. An absolute count on a growing table would warn forever.
- Tests use `warn`: a gap is information about the data, not a pipeline failure.
- Thresholds (gap > 3, 3% rate) are provisional, calibrated on about 14 hours of history, and will be revisited as history grows.

**Takeaway.** A failing test doesn't necessarily mean the data needs "fixing": here it acted as a detector that helped me understand how the source system behaves, and refine what counts as an anomaly.

### 🇬🇧 Per-station quality profile

A `mart_station_quality` mart classifies each station from its history. As of 2026-09-28 (465 stations): 448 `ok`, 4 with a constant capacity gap, 1 station declared operational but silent (all counters at zero), 9 dormant stations (silent for more than 7 days) and 3 closed stations that still report. The split between "dormant" and "closed but reporting" came from a first classification that proved too coarse: the initial status lumped different situations together. A test also showed that `not_null` is not enough: one station had an empty name, which only a dedicated test catches. Thresholds are provisional dbt variables.

**External check.** I cross-checked three stations against the official app: two are closed for works (reopening announced for October 2026), matching their `closed_but_reporting` status; the third, which has no name in the feed (the empty-name test flagged it), is closed until the end of 2026 and appears as `dormant`. "Dormant" therefore also covers temporary closures, and the API provides neither a reason nor a reopening date: the classification describes the feed's behaviour, not its cause. Three hand-picked stations are consistent with the classification but are not a statistical validation. Also, `last_reported` does not appear to be a reliable liveness signal for a healthy station (median 6 h, maximum 8.8 h among `ok` stations), which makes the dormancy threshold (7 days) insensitive to it.