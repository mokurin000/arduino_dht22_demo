#!/usr/bin/env python3

import polars as pl
from pyecharts import options as opts
from pyecharts.charts import Line

CSV_FILE = "records.csv"
OUTPUT_FILE = "records.html"

# 读取 CSV
df = (
    pl.read_csv(CSV_FILE)
    .with_columns(
        pl.col("localtime")
        .str.to_datetime(format="%Y-%m-%dT%H:%M:%S%#z")
        .dt.offset_by("8h")
    )
    .sort("localtime")
)

# pyecharts 需要 Python list
x = df["localtime"].dt.strftime("%Y-%m-%d %H:%M:%S").to_list()

temperature = df["temperature"].to_list()
humidity = df["humidity"].to_list()

line = (
    Line(
        init_opts=opts.InitOpts(
            width="1600px",
            height="800px",
        )
    )
    .add_xaxis(x)
    .add_yaxis(
        "Temperature (°C)",
        temperature,
        is_symbol_show=False,
        is_smooth=False,
        yaxis_index=0,
    )
    .extend_axis(
        yaxis=opts.AxisOpts(
            name="RH (%)",
            type_="value",
            position="right",
            min_=0,
            max_=100,
        )
    )
    .add_yaxis(
        "RH (%)",
        humidity,
        is_symbol_show=False,
        is_smooth=False,
        yaxis_index=1,
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title="DHT22 Records",
            pos_left="center",
        ),
        legend_opts=opts.LegendOpts(
            pos_right="20px",
            pos_top="10px",
        ),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        xaxis_opts=opts.AxisOpts(
            type_="category",
            boundary_gap=False,
            axislabel_opts=opts.LabelOpts(rotate=30),
        ),
        yaxis_opts=opts.AxisOpts(
            name="Temperature (°C)",
            type_="value",
        ),
        datazoom_opts=[
            opts.DataZoomOpts(
                type_="inside",
                xaxis_index=0,
            ),
            opts.DataZoomOpts(
                type_="slider",
                xaxis_index=0,
            ),
        ],
    )
)

line.render(OUTPUT_FILE)

print(f"Saved to {OUTPUT_FILE}")
