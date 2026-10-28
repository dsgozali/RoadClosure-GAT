# Road Access Closure Permit - General Access Time

Streamlit application for exploring Queensland road traffic access windows. It presents road information, a lane-closure matrix, cell-level calculation details, and a PDF export view.

## Scope

The application currently provides:

- **Home** — a map and road coordinate table from the road shapefile, with available roads filtered by the selected region.
- **Table View** — hourly values by road, description, direction, and day type. Select a numeric hour cell to see the source values and lane calculation in the sidebar.
- **PDF View** — a generated matrix with an option to export it as a PDF.

The displayed lane value is a simple heuristic: the app calculates the 85th percentile of the relevant traffic values and converts it to a lane count using `int(percentile // 1000) + 1` (or zero when the percentile is zero). It is not a traffic-engineering model.

## Initialization

### Prerequisites

- Python installed and available on your command line.
- The project dependency versions listed in `requirements.txt`.
- The traffic workbook at `assets/qld-traffic-data-average-by-hour-by-day-2025.xlsx`.
- For the Home map, the road shapefile and its companion files under `assets/QLD_CTRL/`.

### Windows PowerShell

From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run main.py
```

Streamlit prints a local URL in the terminal; open it in a browser to use the app. To stop the server, press `Ctrl+C` in the terminal.

If the workbook cannot be loaded, the matrix data loader falls back to sample data. The Home map displays a warning when the shapefile is unavailable. The region selector and other pages depend on the workbook's expected columns.

## How to use

1. Start the app using the command above.
2. Select a region from the sidebar where region data is available.
3. Use **Home** to inspect the available road map and coordinates.
4. Open **Table View**, choose a road using the page number, then select a numeric hour cell. The sidebar shows the selected road, description, direction, day type, hour, source traffic values, percentile, and lane-count calculation.
5. Open **PDF View** to view the generated matrix and use its export button when available.

## Tests

The fundamental functionality tests are in `tests/test_racp.py`. They cover matrix loading and its sample-data fallback, missing-shapefile behavior, percentile logic, hour formatting, matrix row creation, and traceability inputs/calculation.

Install `pytest` in the active environment if it is not already available, then run from the project directory:

```powershell
python -m pip install pytest
python -m pytest
```

The app's data and visual rendering require the associated dependencies and assets. The tests focus on core logic and do not validate the live Streamlit interface or external operational suitability.

## Disclaimer

This application is an exploratory tool, not an official permit decision, traffic-management plan, safety assessment, or engineering recommendation. Its lane values are derived from supplied traffic data using a simplified heuristic and may not reflect real-world road conditions, capacity, closures, or current regulations. Verify source data and all outputs with the responsible road authority and qualified professionals before using them to plan or authorize work. The sample-data fallback is for demonstration and must not be used for operational decisions.