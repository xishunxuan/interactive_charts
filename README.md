# Data Visualization System

This project provides an interactive data visualization web application for exploring shared bicycle usage data using FastAPI, Altair, and Jinja2 templates.

## Features

- Linked scatter and bar chart: Brush temperature to filter trips per city.
- Interactive legend chart: Click on a country to filter duration vs. trips.
- Duration–trip explorer: 2D brush to select by trip duration and see totals per city.
- Geospatial map with histogram: Brush longitude on map to filter trip duration distribution.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/xishunxuan/interactive_charts.git
   ```

2. Create and activate a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\\Scripts\\activate   # Windows
   ```

3. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

1. Place your processed CSV data file named `bikes_data.csv` in the project root directory.
2. The CSV should contain at least the following columns:
   - `Country`
   - `City`
   - `Month`
   - `Num_Trips`
   - `Avg_Temperature_C`
   - `Avg_Duration_Minutes`
   - `Latitude`
   - `Longitude`

## Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn __main__:app --host 0.0.0.0 --port 8000 --reload
```

Open your web browser and navigate to `http://localhost:8000` to view the home page.

## Endpoints / Visualizations

- `/viz/scatter-bar`: Bike Usage: Temperature vs. Trips (Linked Scatter & Bar)
- `/viz/interactive-legend`: Bike Usage: Duration vs. Trips (Interactive Legend)
- `/viz/duration-explorer`: Bike Usage: Duration/Trips Explorer (Linked to City Totals)
- `/viz/map-histogram`: Bike Usage: Geospatial Map linked to Duration Histogram

## Project Structure

```
├── __main__.py                # FastAPI application
├── templates/
│   └── visualization_page.html  # Jinja2 template for charts
├── bikes_data.csv             # Processed data file (user-supplied)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## License & Author

© {{ "now" | date("Y") }} Created by Xishunxuan. All rights reserved.
