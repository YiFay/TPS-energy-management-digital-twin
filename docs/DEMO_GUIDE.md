# Six-minute demonstration guide

Use this as a rehearsal outline after you understand the assumptions and calculations. Be explicit that implementation was AI-assisted and the dataset is synthetic. Avoid claiming independently authored coding expertise or measured savings.

## 0:00–1:00 — Engineering context

Open Digital twin, choose Cutaway, rotate the station and select an electrical building or pump. Explain that the model connects an engineering asset hierarchy to energy data. Its six-pump deep-shaft arrangement is schematic; geometry is not being used as an accurate BIM or storage-volume measurement.

Show that total station flow, single-pump flow and the common-pipe system curve have different meanings. The shared friction term uses total discharge.

## 1:00–2:00 — A useful drill-down

Select MV electrical rooms in the 3D view, open its analysis, then open HV-01. Show:

- Which system boundary the equipment belongs to.
- Electrical input, duty count and schedule.
- Weather-linked HVAC demand and the difference between an assumed room signal and a thermal simulation.
- The separate accounting for central cooling, motor losses and HVAC.

A useful engineering question: “Could a reported reduction be a changed boundary or reduced service rather than better efficiency?”

## 2:00–3:00 — Data judgement

Data studio → Try m³/h mapping example → Validate & preview. Explain column mapping, conversion, duplicate checks, duration-weighted energy and coverage. Show the invalid example being rejected. Reset demo before continuing so four stages remain available.

Explain that actual project Excel data was deliberately not reproduced in this public-facing portfolio dataset.

## 3:00–4:00 — Analysis rather than decoration

Deviation analytics displays an injected synthetic +8% demand event from 14:00 to 16:00. The regression uses Q × H and outdoor temperature. It trains on the earlier half of the day and evaluates the later half. Show the residual threshold and 24 flagged intervals.

Discuss plausible checks: changed auxiliary load, changed operating conditions, meter calibration, head measurement, model assumptions. The residual is evidence for investigation, not a verified cause or a guaranteed saving.

## 4:00–5:00 — Decision with service checks

Run the efficiency scenario. The default illustrative case maintains hydraulic delivery and inventory while changing conversion efficiencies. Discuss the service gate before the cost numbers. Annual finance needs an explicit repeated-day assumption.

Compare storage and tariff-aware strategies. They are heuristics; they can produce small, negative or negligible benefits. A tariff reduction alone does not prove lower electricity use.

For a contrasting case, select Ultimate + / High in the hydraulic comparison. The synthetic model reports a service shortfall. Do not claim this is a defect in the real project: it is a consequence of the chosen synthetic demand and reference envelope.

## 5:00–6:00 — Reproducibility and next steps

Export the report, interval CSV and portable workspace JSON. Open the evidence register. Explain what would be needed for a production deployment:

- Validated asset register, load list and agreed metering boundary.
- Guaranteed pump curves, NPSHa and transient/availability constraints.
- Calibrated SCADA observations, seasonal inputs and baselines.
- Approved geometry and linked asset IDs.
- Access controls, cybersecurity, operations integration and independent validation.

## Questions to prepare for

| Question | What to explain |
| --- | --- |
| Why does head matter? | Hydraulic power is proportional to Q × H, before conversion losses. |
| Why can single-pump and station curves not be mixed? | Parallel pumps share head and split flow; the common pipe carries total flow. |
| What does kWh/m3 hide? | Head, operating regime, auxiliary boundary and water service can change the ratio. |
| Does improving power factor save the modeled kWh? | No direct effect here; PF changes apparent power. |
| Why use a holdout? | Fitting and evaluating on the same observations can overstate predictive ability. |
| What does AI contribute? | Implementation assistance and iteration; engineering assumptions and outputs still need review. |
| Is this a digital twin? | It is a spatially linked planning prototype. It lacks a validated live connection and operational feedback. |
| What did you personally do? | Describe only your real requirements work, analysis, checks, learning and decisions. |
