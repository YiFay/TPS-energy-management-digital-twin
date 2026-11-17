# Engineering model and assumptions

## Purpose and boundary

A representative-day energy planning and analysis prototype, not a live operational digital twin. All six pump trains are installed in the modeled fleet. The selected available count can be reduced for availability scenarios. In the default boundary, regional odour control is excluded; selecting TPS + network adds it explicitly.

Each interval carries duration, total inflow, total discharge, head, active train IDs, speed, electrical demand, storage change, spill, tariff and system/asset/zone allocations. Electricity is integrated as `sum(kW × hours)` and water as `sum(m3/s × 3600 × hours)`.

## Pump and system equations

- Hydraulic power: `P_hyd(kW) = rho × g × Q × H / 1000`, with rho = 1000 kg/m3 and g = 9.81 m/s2.
- Shaft power = hydraulic power / pump efficiency.
- Main electrical input = shaft power / motor efficiency / VFD efficiency.
- For n identical parallel trains, each receives `Q_total / n` at the same head.
- Shared friction is interpolated from the **whole-station total-flow curve**, never from per-pump flow.
- The synthetic system curves use static-head assumptions 76 / 82 / 88 m and sampled friction `0.025 × Q_total²`. The executable model interpolates the CSV points linearly; it does not override imported curves with that equation.
- Water-level feedback changes static lift by the negative of the relative level change from its initial value.
- Reference-speed ratio `s = nominal_speed / 0.941`. Affinity scaling is `Q = s × Qref`, `H = s² × Href`. Efficiency is interpolated at `Q/s` and optionally multiplied by a scenario factor.
- No interpolation outside supplied pump or system curve ranges is allowed.

The supplied manufacturer proposal states the duty anchor 3.08 m3/s, 90 m, 90% pump efficiency. The bundled expected-curve shape is a visual approximation, not certified digitization or a guaranteed acceptance curve. Nominal speed bounds 70–94.1%, a reference continuous-flow band 2.05–3.65 m3/s and a 3,900 kW per-train shaft-power cap are used. The flow band is an **assumption**, not an OEM-approved operating envelope. Pump efficiency is not a blanket guarantee at all operating conditions.

## Scheduling and storage

Candidate counts are constrained by available trains, minimum run time and minimum off time. Among feasible counts at a requested total discharge, the model chooses minimum estimated electrical input. It retains existing trains where possible and uses accumulated runtime to prioritize eligible trains. This is not a globally optimal scheduling algorithm or a comprehensive maintenance rotation policy.

The default effective wet-well area is 900 m2. Its relative operating band is 1–5 m with an initial level of 3 m. These are independent simulation assumptions, not the full structural shaft volume or absolute project elevations.

For an interval of dt seconds:

`V_end = V_start + (Q_in − Q_out) × dt − V_spill`

The lower bound limits the maximum discharge. Infeasible requested discharge triggers a finite search over feasible lower/nearby flows. If no constrained point exists, pumps stop; a minimum-run override is reported. Water exceeding the upper storage limit is recorded as **modeled spill**. It does not establish actual flooding, tunnel surcharge or downstream consequences.

Three heuristics are available:

1. Demand following: target the initial water level with a 900-second feedback horizon.
2. Storage smoothing: use a slower 2,400-second level feedback horizon.
3. Tariff-aware: use a lower inventory target during cheaper intervals and a higher target during expensive intervals. This is a simple inventory-based heuristic, not an optimal-control solver.

All modes recover toward initial level during the final hour with a 600-second horizon. The independent balance check is inflow minus discharged water, spill and storage change. Minimum run/rest rules are enforced on interval boundaries; sub-interval switching is not simulated.

## Auxiliary accounting

Base auxiliary demand is input kW per duty unit × duty units × load factor × schedule. Only energized duty units are counted. Generic stage multipliers are 0.82 / 0.91 / 1.00 / 1.08 for applicable auxiliary groups.

Schedules are continuous; daytime 07:00–19:00 with 18% otherwise; night before 06:00 and from 18:00 with 12% otherwise; or an illustrative intermittent duty during the first 15 minutes of each hour. Intermittent values are evaluated at the interval start. They are not detailed drainage/process control simulation.

### HVAC

Six illustrative zones: MV electrical rooms, control/SCADA, administration/welfare, motor/drive gallery, maintenance workshop and service/access rooms. Zone areas and setpoints are assumptions. Electrical demand is adjusted by a bounded outdoor-temperature response `clamp((Tout − 20)/16, 0.55, 1.5)` and `3.4 / selected COP` at the same assumed thermal duty. This is a planning approximation, not a calibrated building-load model. The room-temperature traces are explicitly illustrative signals and do not prove comfort or equipment thermal compliance.

### Central cooling

Thermal duty = `650 × stage_multiplier + 0.75 × main_motor_loss_kW`.

Chiller electricity = thermal duty / COP. Cooling circulation and heat rejection are separate electrical groups. Cooling-water flow is thermal duty / (4.186 × deltaT), in L/s with water density approximated at 1 kg/L. Default deltaT is 5 K. The chiller group's load-register input is a reference capacity, while its operating demand follows thermal duty/COP. Over-capacity requests are flagged; no hidden clipping is used.

The synthetic HVAC circuit is treated as separate from central equipment cooling. Motor/VFD conversion losses are already part of main electrical input and are not added again as independent electrical loads. Extracting their heat requires additional cooling electricity, which is distinct.

### Odour control and ventilation

Fan efficiency scenarios preserve the same inferred air duty. For the TPS extraction fans, estimated airflow is electrical input × assumed total fan efficiency / assumed pressure drop. The default pressure drop is 3,500 Pa; a separately declared 150,000 m3/h minimum is screened. Neither value is measured or a contractual limit. Air-treatment effectiveness, H2S, removal efficiency, room safety and duct-network performance are not solved. Safety ventilation and scrubber circulation are not reduced by an energy-saving slider.

### Electrical and other systems

RW polishing, self-cleaning, drainage, controls, instruments, communication, CCTV, internal/external lighting, transformer and UPS losses have separate groups. The distribution/UPS-loss groups are upstream allowances, excluding the motor and VFD losses already embedded in main input. Power factor affects apparent power (`kVA = kW/PF`), not electrical kWh directly.

If requested auxiliary electrical input exceeds its assumed rated-duty input, the interval is flagged. Demand is retained for transparency; such a scenario is not accepted as a service-preserving investment case.

## Statistical analysis

Meter data remains separate from planning inputs. Join by minute and equal interval duration; unmatched observations are reported and excluded. At least 20 aligned intervals are required. The first half trains ordinary least squares:

`Electrical kW = beta0 + beta1 × (measured flow × measured head) + beta2 × outdoor temperature`.

The second half is held out. RMSE and R2 refer to that held-out set. A singular feature matrix is rejected. The residual threshold is `max(3 × training RMSE, 3% × abs(predicted kW))`. Only held-out exceedances are flagged. Positive physics deviations are descriptive differences, not verified avoidable energy. Autocorrelation, one-day coverage and the simple feature set limit generalization; the 24 injected-event detections demonstrate the mechanism, not validated diagnostic accuracy.

## Scenario economics

A case is comparable only when both baseline and alternative have no modeled spill (below 1 m3), no minimum-run protection overrides, no auxiliary-rating exceedances, no assumed OCU airflow shortfalls and terminal-inventory/delivered-volume differences below 1% of baseline usable storage.

Annual cash flow = daily illustrative cost difference × equivalent operating days − additional annual maintenance. Simple payback = investment / positive annual cash flow. NPV discounts each equal annual cash flow over the entered whole-year period. Annual results require explicit acknowledgement of the repeated-day assumption. No seasonality, escalation, degradation, demand charges, replacement cost, tax or terminal value is modeled. Even a passed service screen is not engineering approval.

## Geometry and source relationship

The eight-page supplied TPS layout/section PDF informs the connected deep-shaft arrangement. Plan page 2 and sections on pages 7–8 were visually reviewed. The code creates original schematic meshes, compressed in depth, with conceptual buildings and skids. It neither embeds the PDF nor reconstructs an engineering-accurate BIM model. The requested six-pump scope is used despite apparent additional bays in the tender drawing. Spatial dimensions and room grouping must not be used for design or quantity takeoff.

The provided original actual-project spreadsheets are not reused in the bundled dataset. The manufacturer's expected curve is acknowledged as approximate input; original source files and company logos are excluded from the package.
