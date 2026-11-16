# Validation record

Date: 16 November 2026. Runtime: Python **3.12.14**. Target user's runtime: Python 3.15.2 on Windows. This is a standard-library-only application with intended modern Python 3 compatibility; no Windows / Python 3.15.2 on-device test was possible.

## Automated checks

21 tests pass with `python -m unittest -v test_engine.py`:

- Water and electrical-energy conservation in all twelve stage/head combinations.
- Independent rho-g-Q-H electrical-input equation and per-train shaft cap.
- Common-pipe friction evaluated on total station discharge.
- Auxiliary asset / system / HVAC-zone reconciliation.
- Minimum on/off intervals in a tariff-aware case.
- Reduced pump availability reports unserved/spilled water and blocks a false savings conclusion.
- Power-factor changes leave kWh unchanged.
- Optional network-boundary energy is included exactly once.
- Efficiency comparison preserves delivered volume and terminal storage.
- Storage and tariff strategies recover terminal inventory within the configured tolerance.
- Central cooling heat/COP linkage and separate motor/VFD losses.
- Rejection of non-finite, duplicate, negative and incomplete inflow data.
- CSV column mapping and m3/h flow conversion.
- Malformed CSV headers and inconsistent row widths are rejected.
- MW-to-kW conversion for imported auxiliary loads.
- Imported common-system curves actually alter the calculation.
- Chronological regression split and injected-event screening.
- Invalid model parameters are rejected.
- Auxiliary electrical overload blocks the same-service comparison.
- Fan efficiency changes preserve the assumed air duty.
- Local HTTP responses, session-token protection and source-path denial.

`node --check` passes for the application, chart and 3D JavaScript files. Node is a development check only and is not needed to run the delivered application.

## Browser verification

The application was run in the managed preview and inspected in a real Chromium browser, including screenshots. Verified workflows:

- Initial model loading and rendering of the interactive 3D station.
- Selecting an electrical building directly in the canvas updates the asset inspector.
- Opening the HVAC zone and its equipment detail page.
- Energy charts, the 11-system hourly heatmap and system contributions.
- Statistical analysis renders 288 aligned observations, 144 training / 144 test intervals and the 24 seeded-event flags.
- m3/h sample: column mapping, normalization, range/coverage preview, applying the table and recalculation.
- Active inflow CSV was downloaded and uploaded through the real file chooser; all 1,152 rows and four 24-hour stages passed validation.
- Invalid CSV: duplicate interval displayed; Apply is disabled.
- Reset demonstration restores the original four-stage input.
- Efficiency scenario: service gate, matching volume, finance acknowledgement and calculated results.
- Scenario JSON produces a browser download.
- All twelve hydraulic stage/head cases are shown; the synthetic Ultimate_plus / High case reports spill.
- OCU system detail shows the assumed air-duty and pressure context.

The browser checks are interactive workflow checks, not a claim of exhaustive browser/device coverage. Responsive styles are included; a separate physical mobile device and the user's Windows installation were not tested.

## Scientific and engineering limits

Passing software tests means consistency within this model, not validation against an operating station. No real SCADA calibration, manufacturer acceptance verification, independently verified saving, climate-year validation, pressure-transient model, NPSHa check, H2S treatment performance or approved BIM geometry is established.

The duty curves, auxiliary register, temperature signals, service thresholds and annual repetition assumptions must be reviewed or replaced before professional engineering use. Refer to `docs/MODEL.md` for the exact implemented assumptions.
