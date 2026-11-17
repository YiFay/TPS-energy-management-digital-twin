# Data dictionary

## Shared conventions

CSV is UTF-8, optionally with a BOM. Import up to 5 MB and 15,000 rows per table. Column names can be mapped in the UI. Units are normalized explicitly; they are not guessed from numeric magnitude.

- Flow inputs: m3/s, m3/h or L/s, normalized to m3/s.
- Electrical power inputs: kW or MW, normalized to kW.
- Pump efficiency: fraction or percent, normalized to a fraction.
- Duration: hours, including non-uniform intervals.
- Time: integer minute-of-day (0–1439), HH:MM, or a timezone-qualified ISO timestamp. ISO timestamps convert to UTC; multiple resulting UTC dates are rejected. Seconds must be zero. HH:MM is representative profile time without an implicit calendar date.
- Stage identifiers: `COD`, `Expiry`, `Ultimate`, `Ultimate_plus`.
- A full contiguous 24-hour inflow profile is required for the selected stage. Gaps are rejected before storage simulation. Other stages can be absent; the comparison uses available data.
- A table import replaces that entire table. It does not append rows or merge four stages automatically.
- `provenance` is optional in stored CSVs. The import form supplies a declared source string for normalized imported rows. It is not independent verification.

## Inflows: `inflow_profiles.csv`

| Field | Unit / values | Interpretation |
| --- | --- | --- |
| stage | Four canonical identifiers | Development scenario |
| minute | Minute of representative day | Interval start |
| duration_h | Hours | Interval duration; must not cross midnight |
| inflow_m3s | m3/s | Total station inflow, not per-pump flow |

Bundled means are independently selected at 5.2 / 8.0 / 10.8 / 14.2 m3/s. Each stage has 288 five-minute intervals. The smooth diurnal shape is an original synthetic function. Duplicate stage/time keys, negative flow, non-finite values and overlap are rejected.

## Single-pump curve: `reference_pump_curve.csv`

| Field | Unit | Interpretation |
| --- | --- | --- |
| q_m3s | m3/s | Single-pump flow at reference speed |
| head_m | m | Expected head at that flow |
| pump_efficiency | Fraction (0–1) | Pump conversion efficiency |
| reference_speed_pct | % (metadata) | Bundled reference: 94.1% nominal |

At least three distinct flow points are needed. The executable reference-speed assumption is fixed at 94.1%; changing the metadata cell alone does not alter it. Low-flow illustrative points do not authorize operation outside the assumed continuous-flow envelope. Imported curves must use that same reference speed or the engine must be adapted. No extrapolation is allowed.

## Shared system curves: `shared_system_curves.csv`

| Field | Unit / values | Interpretation |
| --- | --- | --- |
| head_case | Low / Normal / High | Static-lift scenario |
| total_flow_m3s | m3/s | Whole-station discharge |
| static_head_m | m | Constant within a case |
| shared_friction_m | m | Common-pipe loss at total flow |
| total_head_m | m (optional metadata) | Bundled sum of static and friction |

The engine recomputes total head from static lift, wet-well level and interpolated friction. It does not use a stale optional `total_head_m` field. At least three unique flow points per supplied case are required. Include zero and enough high-flow coverage for the intended operating region.

## Auxiliary groups: `auxiliary_loads.csv`

| Field | Values / unit | Interpretation |
| --- | --- | --- |
| asset_id | Unique text ID | Load-group identifier |
| system | Defined system name | Accounting category |
| name | Text | Human-readable equipment group |
| zone_id | Text | HVAC-zone reference or schematic area code |
| boundary | TPS / Network | Energy-accounting boundary |
| input_kw | kW per duty unit | Rated/assumed electrical input; not shaft output |
| duty_units | Whole number | Number of energized duty units |
| load_factor | Fraction, 0–1 | Mean input fraction before modifiers |
| schedule | continuous / daytime / night / intermittent | Duty pattern |

Allowed systems: HVAC; Ventilation; Odour control; Regional odour; Central cooling; Water services; Auxiliary pumping; Controls and ICT; Buildings and lighting; Electrical losses. Main pumping is computed from hydraulics and is not entered again in this table.

HVAC loads must reference a declared HVAC `zone_id`. The group `CW-CH` is the central chiller: its actual demand is computed from thermal duty/COP; the input/duty values provide an assumed electrical capacity check. Names containing “fan” within Odour control / Regional odour activate the fan-efficiency adjustment. Keep these conventions when editing or adapt the code for a different asset taxonomy.

## HVAC zones: `hvac_zones.csv`

| Field | Unit | Interpretation |
| --- | --- | --- |
| zone_id | Unique text | Join key for HVAC equipment |
| name | Text | Region/room-group name |
| level | Text | Schematic deck label |
| area_m2 | m2 | Assumed area for context; not used as a heat-load solver input |
| setpoint_c | °C | Reference for illustrative room signals |
| max_temp_c | °C | User-defined review line; not a compliance limit |

The 3D scene has six fixed schematic zones. Additional imported zones appear in data and analysis but do not automatically generate new geometry.

## Weather and tariff: `weather_tariff.csv`

| Field | Unit | Interpretation |
| --- | --- | --- |
| minute | Minute | Effective start of record |
| outdoor_c | °C | Outdoor-temperature assumption |
| tariff_aed_kwh | AED/kWh | Interval electricity rate |

The first record must start at minute 0. Values are held until the next record; this is deliberate stepwise resampling. The bundled tariff is illustrative (0.28 / 0.35 / 0.46 AED/kWh), not a statement of current UAE utility pricing. A flat-tariff mode is available in Model inputs.

## Meter signal: `demo_meter_readings.csv`

| Field | Unit | Interpretation |
| --- | --- | --- |
| minute | Minute | Observation interval start |
| duration_h | Hours | Observation duration |
| measured_kw | kW | Imported signal; bundled values are synthetic |
| flow_m3s | m3/s | Corresponding total discharge |
| head_m | m | Corresponding head |
| provenance | Text | Declared origin |

The filename and column `measured_kw` describe the schema, not the truth status of bundled observations. Bundled rows explicitly say SYNTHETIC. Physics comparison is meaningful only for matching development stage, head, configuration, boundary and time context. No imputation occurs. At least 20 matching rows are needed for the regression.

## Main output fields

| Field | Unit | Interpretation |
| --- | --- | --- |
| main_kw / aux_kw / total_kw | kW | Disjoint electrical demand components |
| energy_kwh | kWh per interval | Total electrical energy |
| water_m3 | m3 per interval | Delivered discharge volume |
| level_start_m / level_end_m | Relative m | Effective wet-well state |
| overflow_m3 | m3 | Above-bound storage spill |
| active_ids | ID list | Trains energized that interval |
| speed_pct | % nominal | Common train speed |
| pump_eta | Fraction | Current interpolated pump efficiency |
| motor_loss_kw / vfd_loss_kw | kW | Already contained in main input |
| cooling_heat_kw | kW thermal | Assumed cooling requirement |
| cooling_flow_ls | L/s | Thermal-duty flow at configured deltaT |
| odour_airflow_m3h | m3/h | Inferred fan air duty at assumed pressure drop |
| overloaded_assets | ID list | Requested electrical input above assumed rating |
| systems / assets / zones | Nested kW maps | Reconciled allocations |
| zone_temps | °C map | Illustrative signals, not thermal-model outputs |

The simple interval CSV excludes nested maps; the full calculation JSON preserves them. Residual CSV and scenario JSON are separate evidence exports.
