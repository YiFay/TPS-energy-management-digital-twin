# TPS Twin Studio

An interactive, spatially linked pumping-station energy planning prototype. It combines a six-train hydraulic model, auxiliary-load accounting, a navigable 3D station, CSV quality gates and statistical deviation analysis.

**Original synthetic datasets. AI-assisted implementation. No live SCADA connection or automatic control.**

## Run locally

On Windows, extract the entire archive and double-click **Start_Windows.bat**. Keep the console window open. The launcher prefers Python 3.15 and falls back to an available Python 3 interpreter.

On other systems, run `python3 app.py`. The server binds to `127.0.0.1`, chooses a free port and opens a browser. A modern browser is required. No pip packages, JavaScript package installation, CDN, account or network connection is needed.

Python 3.15 compatibility is intended through standard-library-only implementation. Actual validation environment and browser checks are recorded in [VALIDATION.md](VALIDATION.md); the user's Windows / Python 3.15.2 machine was not available for testing.

## Explore

| Workspace | Functional scope |
| --- | --- |
| Digital twin | Perspective 3D mesh viewer; orbit and zoom; site, cutaway and plan views; hover information; object selection; energy-state layer; timeline playback; accessible asset selector |
| Energy performance | Demand, system energy composition, hourly heatmap, flow-power and flow-specific-energy scatter, cost by time block, load-duration curve |
| Systems & assets | 11 system categories, 26 auxiliary groups, six HVAC zones; station → system → zone → equipment routes; dedicated cooling and OCU service context |
| Hydraulics & storage | Six pump trains; shared system resistance; speed and shaft limits; effective wet-well storage; minimum on/off times; water balance; 12 stage/head cases |
| Deviation analytics | Imported or synthetic meter signal; physics comparison; chronological training/test split; explainable regression; residual screening; evidence export |
| Scenario lab | Efficiency, storage and tariff-aware scenarios; same-service gate; auxiliary rating and assumed OCU air-duty checks; conditional payback and NPV |
| Data studio | Seven CSV types; drag/drop or browse; manual column mapping; unit normalization; data preview; duplicate/overlap/range checks; portable workspace JSON |
| Reports & evidence | Interval CSV, full calculation JSON, Markdown report, residual CSV, scenario JSON, workspace restore and browser print/PDF |

The 3D renderer and SVG chart library are original local JavaScript, not external visualization dependencies. The scene is a **schematic interpretation**, not an IFC, CAD or BIM import. Geometry does not drive the hydraulic storage volume.

## Try the data workflow

1. Open **Data studio → Try m³/h mapping example**.
2. Inspect the proposed mappings: `time → minute`, `hours → duration_h`, `flow_m3h → inflow_m3s`.
3. Select m³/h, validate, and check the normalized flow range and 24-hour coverage.
4. Apply only after reviewing the preview. This replaces the entire inflow table with a COD-only example.
5. Try the invalid-data example to see a duplicate interval rejected. No silent repair is applied.
6. Use **Reset demo** to restore all four stages.

Data imports live in the page session, not in a server database. Save a workspace JSON before refreshing or closing. Restore it through Data studio to reproduce your analysis. Imported filenames and declared provenance are carried into the workspace.

## Reproducible demonstration

The bundled meter CSV is generated from the default COD / Normal / demand-following model, with deterministic noise and an injected +8% excess load between 14:00 and 16:00. It is **not real meter data**. The first 144 intervals train the regression; the second 144 are held out. The default result flags the 24 injected-event intervals. This does not establish general fault-detection accuracy.

The `Ultimate_plus / High` synthetic case exceeds modeled hydraulic service capacity. It intentionally illustrates why low energy must not be mistaken for better performance when less water is served. It is not a finding about the actual project.

## Inputs, model and scope

- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Engineering model and assumptions](docs/MODEL.md)
- [Six-minute demonstration guide](docs/DEMO_GUIDE.md)
- [Validation record](VALIDATION.md)
- [中文启动说明](START_HERE_CN.txt)

The original project inflow and pipe-loss workbooks, source drawings and manufacturer PDF are **not bundled**. Inflow, shared resistance, auxiliary loads, zone areas, weather, tariff and meter observations are synthetic. The reference pump curve uses an explicit duty anchor and an approximate expected-curve shape, with its provenance recorded in the CSV.

The supplied layout shows a deep circular shaft, a separate inlet/screen shaft, wet and dry zones and multiple decks. The demonstration preserves these relationships with compressed depth and adopts the requested six-pump configuration. Additional apparent drawing bays are not claimed as installed assets. External buildings and HVAC subdivisions are illustrative.

## Source structure

- `app.py`: local HTTP server, CSV normalization and API routing.
- `engine.py`: hydraulic, storage, auxiliary-energy and regression calculations.
- `generate_data.py`: generates auxiliary/zone/weather/meter demonstration datasets using the bundled synthetic hydraulic inputs.
- `static/`: English application, styles, charts and original 3D renderer.
- `data/`: seven active CSV datasets and two import examples.
- `test_engine.py`: independent physical, validation and API checks.
- `example_outputs/`: reproducible example results from the bundled defaults.
- `docs/`: technical assumptions, schemas and presentation guidance.

## Verification

Run `python -m unittest -v test_engine.py` from the project folder. The tests check independent water/energy balances, shaft power, parallel-flow accounting, service constraints, unit conversion, data rejection, imported-curve use, regression split and HTTP protections.

## Using GitHub

The folder is ready to use as a source repository. Upload original code, synthetic CSVs, documentation and tests. The included `.gitignore` excludes temporary runtime files and conventional private-data folders. Actual client data requires your own authorization and review before any publication.

**GitHub Pages does not execute Python.** For this version, demonstrate the locally running application or a screen recording. Internet hosting would require a Python-capable service and a separate deployment configuration. This delivery does not publish the application or change repository access.

## Responsible presentation

Explain your role in defining the engineering question, setting assumptions, checking equations, interpreting evidence and iterating with AI assistance. Do not present simulated savings as measured project outcomes, the 3D schematic as an as-built digital twin, or generated code as proof of independent software-engineering mastery.

Original code and synthetic data are provided under the included MIT license. No source OEM/project documents, trademarks or company endorsement are included.
