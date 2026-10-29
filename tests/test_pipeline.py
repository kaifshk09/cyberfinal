import io
import pandas as pd
import pytest
from src.traffic_pipeline import load_data, summarize_data, REQUIRED

def test_load_data_valid():
    data = "timestamp,road,location,vehicle_count,avg_speed_kmph,weather\n2026-01-01 08:00:00,Main Road,Central,100,22,Clear\n"
    df = load_data(io.StringIO(data))
    assert len(df) == 1
    assert df.iloc[0]["vehicle_count"] == 100

def test_missing_columns_raise():
    with pytest.raises(ValueError, match="Missing required"):
        load_data(io.StringIO("timestamp,road\n2026-01-01,Main\n"))

def test_invalid_rows_dropped_and_negative_count_clipped():
    data = "timestamp,road,location,vehicle_count,avg_speed_kmph,weather\n2026-01-01,Main,Central,-5,30,Clear\nbad date,Main,Central,10,30,Clear\n"
    df = load_data(io.StringIO(data))
    assert len(df) == 1
    assert df.iloc[0]["vehicle_count"] == 0

def test_summarize_data_keeps_columns():
    df = pd.DataFrame([{ "timestamp": pd.Timestamp("2026-01-01"), "road":"A", "location":"B", "vehicle_count":2, "avg_speed_kmph":30, "weather":"Clear"}])
    assert list(summarize_data(df).columns) == REQUIRED
