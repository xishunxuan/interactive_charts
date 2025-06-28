import pandas as pd
import numpy as np
import altair as alt
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# For Visualization 4, to get world map data
from vega_datasets import data as vega_data  # Renamed to avoid conflict if user has local 'data'

# Initialize FastAPI app
app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# read processed data
df_bikes = pd.read_csv("bikes_data.csv")

#%%
# --- Altair Chart Definitions ---

def create_linked_scatter_bar_chart(data: pd.DataFrame):
    # (Same as before - for brevity, I'll assume it's here)
    brush = alt.selection_interval(encodings=['x'])
    scatter_plot = alt.Chart(data).mark_point().encode(
        x=alt.X('Avg_Temperature_C:Q', title='Avg. Temperature (°C)'),
        y=alt.Y('Num_Trips:Q', title='Number of Trips'),
        color=alt.Color('Country:N', legend=alt.Legend(title='Country')),
        tooltip=['City:N', 'Month:N', 'Num_Trips:Q', 'Avg_Temperature_C:Q']
    ).add_params(brush).properties(
        title='Bike Trips vs. Temperature (Brush Temperature to Filter)',
        width=500, height=300
    )
    bar_chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('sum(Num_Trips):Q', title='Total Trips in Selection'),
        y=alt.Y('City:N', sort=alt.EncodingSortField(field="sum(Num_Trips)", op="sum", order="descending")),
        color='Country:N',
        tooltip=['Country:N', 'City:N', 'sum(Num_Trips):Q']
    ).transform_filter(brush).properties(
        title='Trips per City (Filtered by Temperature Brush)',
        width=500, height=300
    )
    return (scatter_plot & bar_chart).to_json(indent=None)


def create_interactive_legend_chart(data: pd.DataFrame):
    # 1. 定义一个基于“国家(Country)”的单点选择器
    # empty='all' 确保在没有选择任何国家时，显示所有数据。
    country_selection = alt.selection_point(fields=['Country'], empty='all')
    # 2. 左侧的散点图（被控制的图表）
    # 核心改动：使用 .transform_filter() 来根据国家选择器过滤数据
    scatter_plot = alt.Chart(data).mark_circle(size=80).encode(
        x=alt.X('Avg_Duration_Minutes:Q', title='Avg_Duration_Minutes'),
        y=alt.Y('Num_Trips:Q', title='Num_Trips'),
        # 颜色仍然可以按国家区分，在显示所有国家时很有用
        color=alt.Color('Country:N', legend=None),  # legend=None 避免出现多余的图例
        tooltip=['Country:N', 'City:N', 'Month:N', 'Num_Trips:Q', 'Avg_Duration_Minutes:Q']
    ).transform_filter(
        country_selection  # 在这里应用过滤器，实现“只显示”的效果
    ).properties(
        title='Num_Trips_of_conutry',
        width=500, height=300
    )
    # 3. 右侧的条形图（作为交互式图例/控制器）
    # 这个图表的代码与您原始版本非常接近，它是正确的“控制器”设置
    legend_bar_chart = alt.Chart(data).mark_bar().encode(
        y=alt.Y('Country:N', axis=alt.Axis(orient='right', title='Number of Trips')),
        x=alt.X('sum(Num_Trips):Q', title='sum_Num_Trips'),
        # 使用 condition 来高亮被选中的条形，给用户提供清晰的视觉反馈
        color=alt.condition(
            country_selection,
            alt.Color('Country:N', legend=None),  # 选中时，使用国家自身的颜色
            alt.value('lightgray')  # 未选中时，显示为灰色
        ),
        tooltip=['Country:N', 'sum(Num_Trips):Q']
    ).add_params(
        country_selection  # 将选择器绑定到这个图表上，使其能够被点击
    ).properties(
        title='all_country',
        width=200, height=300
    )
    # 4. 将两个图表横向拼接
    final_chart = scatter_plot | legend_bar_chart
    # 5. 返回图表的 JSON 格式
    return final_chart.to_json(indent=None)

# --- NEW VISUALIZATION 3 ---
def create_duration_trip_explorer_chart(data: pd.DataFrame):
    """
    Visualization 3: Scatter plot of Duration vs Trips, linked to a bar chart of Trips per City.
                     Brush on the scatter plot to filter the bar chart.
    """
    brush = alt.selection_interval(name="scatter_brush")  # 2D brush

    points = alt.Chart(data).mark_point().encode(
        x=alt.X('Avg_Duration_Minutes:Q', title='Average Trip Duration (min)', scale=alt.Scale(domain=[0, 60])),
        y=alt.Y('Num_Trips:Q', title='Number of Trips'),
        color=alt.Color('Country:N', legend=alt.Legend(title='Country')),
        tooltip=['City:N', 'Month:N', 'Num_Trips:Q', 'Avg_Duration_Minutes:Q']
    ).add_params(
        brush
    ).properties(
        title='Explore Trips by Duration and Count (Brush to Select)',
        width=500,
        height=300
    )

    bars = alt.Chart(data).mark_bar().encode(
        x=alt.X('sum(Num_Trips):Q', title='Total Trips in Selection'),
        y=alt.Y('City:N', sort=alt.EncodingSortField(field="sum(Num_Trips)", op="sum", order="descending"), title="City"),
        color='Country:N',
        tooltip=['Country:N', 'City:N', 'sum(Num_Trips):Q']
    ).transform_filter(
        brush  # Filter bars based on the brush selection in the scatter plot
    ).properties(
        title='Total Trips per City (Filtered by Selection)',
        width=500,
        height=300
    )

    return (points & bars).to_json(indent=None)


def create_map_linked_histogram_chart(data: pd.DataFrame):
    """
    Visualization 4: Geospatial map of bike usage (city points) linked to a histogram
                     of trip durations. Brush on map longitude to filter histogram.
    """
    map_brush = alt.selection_interval(
        name="map_brush",
        encodings=['longitude'],
        empty=True
    )

    sphere = alt.Chart(alt.sphere()).mark_geoshape(
        fill="transparent", stroke="lightgray", strokeWidth=0.5
    )
    countries_map = alt.Chart(alt.topo_feature(vega_data.world_110m.url, 'countries')).mark_geoshape(
        fill="lightgray", stroke="white", strokeWidth=0.2
    )

    city_points = alt.Chart(data).mark_circle(opacity=0.6, size=50).encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        color=alt.condition(map_brush, alt.value('red'), alt.value('steelblue')),
        size=alt.Size('Num_Trips:Q', scale=alt.Scale(range=[10, 800]), legend=alt.Legend(title="Num Trips (Size)")),
        tooltip=[
            alt.Tooltip('City:N'),
            alt.Tooltip('Month:N'),
            alt.Tooltip('Num_Trips:Q'),
            alt.Tooltip('Avg_Temperature_C:Q', title='Avg Temp (°C)'),
            alt.Tooltip('Avg_Duration_Minutes:Q', title='Avg Duration (min)')
        ]
    ).add_params(
        map_brush
    ).properties(
        width=600,
        height=400,
        title="Global Bike Usage (Brush Longitude to Filter Histogram)"
    )

    left_map = alt.layer(sphere, countries_map, city_points).project(
        type='naturalEarth1'
    )

    base_histogram = alt.Chart(data).mark_bar().encode(
        alt.X('Avg_Duration_Minutes:Q', bin=alt.Bin(maxbins=25), title='Avg. Trip Duration (min)', scale=alt.Scale(domain=[0, 60])),
        alt.Y('count():Q', title='Number of Records')
    ).properties(
        width=250,
        height=350,
        title='Trip Duration Distribution'
    )

    filtered_histogram_overlay = base_histogram.encode(
        color=alt.value('red')
    ).transform_filter(
        map_brush
    )

    right_histogram = alt.layer(
        base_histogram.encode(color=alt.value('steelblue')),
        filtered_histogram_overlay
    )

    return (left_map | right_histogram).to_json(indent=None)


# --- FastAPI Endpoints (Updated with new routes) ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("visualization_page.html", {
        "request": request,
        "chart_title": "Shared Bicycle Data Visualizations",
        "chart_spec": None,
        "show_links": True
    })


@app.get("/viz/scatter-bar", response_class=HTMLResponse)
async def show_scatter_bar_chart(request: Request):
    chart_spec = create_linked_scatter_bar_chart(df_bikes)
    return templates.TemplateResponse("visualization_page.html", {
        "request": request,
        "chart_title": "Bike Usage: Temperature vs. Trips (Linked Scatter & Bar)",
        "chart_spec": chart_spec,
        "show_links": False
    })


@app.get("/viz/interactive-legend", response_class=HTMLResponse)
async def show_interactive_legend_chart(request: Request):
    chart_spec = create_interactive_legend_chart(df_bikes)
    return templates.TemplateResponse("visualization_page.html", {
        "request": request,
        "chart_title": "Bike Usage: Duration vs. Trips (Interactive Legend)",
        "chart_spec": chart_spec,
        "show_links": False
    })


@app.get("/viz/duration-explorer", response_class=HTMLResponse)
async def show_duration_explorer_chart(request: Request):
    chart_spec = create_duration_trip_explorer_chart(df_bikes)
    return templates.TemplateResponse("visualization_page.html", {
        "request": request,
        "chart_title": "Bike Usage: Duration/Trips Explorer (Linked to City Totals)",
        "chart_spec": chart_spec,
        "show_links": False
    })


@app.get("/viz/map-histogram", response_class=HTMLResponse)
async def show_map_histogram_chart(request: Request):
    chart_spec = create_map_linked_histogram_chart(df_bikes)
    return templates.TemplateResponse("visualization_page.html", {
        "request": request,
        "chart_title": "Bike Usage: Geospatial Map linked to Duration Histogram",
        "chart_spec": chart_spec,
        "show_links": False
    })


if __name__ == "__main__":
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)