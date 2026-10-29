# Project report and viva notes

## Abstract
Smart City Traffic Analytics processes timestamped traffic observations to summarize vehicle volume, average speed, road-level trends, and hourly patterns. It presents the results in an interactive dashboard. The bundled dataset is synthetic and is included for reproducible demonstration.

## Objectives
- Explore and clean traffic records.
- Apply PySpark DataFrame aggregation where the environment supports it.
- Compare traffic volume and speed across roads and hours.
- Provide filters and downloadable results.

## Methodology
1. Load CSV data.
2. Validate required columns and types.
3. Remove rows with invalid timestamp/numeric fields.
4. Use PySpark aggregations when available, with Pandas fallback.
5. Visualize results with Plotly and Streamlit.
6. Export filtered records and a summary.

## Limitations
The bundled data is synthetic. It does not represent official Mumbai traffic, a live feed, or a calibrated congestion model. Congestion is illustrated using a project-defined speed threshold of 20 km/h. A future version could use a cited open dataset and benchmark Spark against Pandas at multiple dataset sizes.

## Viva questions
1. What is Big Data? Data whose volume, velocity, and/or variety can require scalable processing tools.
2. Why PySpark? It provides DataFrame operations and distributed processing capabilities.
3. What is ETL? Extract, transform, and load: bringing data in, cleaning/transforming it, and making it ready for analysis.
4. What is a DataFrame? A tabular collection of named columns that can be processed using data tools.
5. Why synthetic data? It makes the demo reproducible without claiming access to a live feed.
6. Does the project predict traffic? No, the current version analyzes supplied historical/sample records.
