# crops/ml/feature_engineering.py

import pandas as pd
import numpy as np

def feature_engineering(df):
    new_df = df.copy()
    new_df['lag1'] = new_df['average_price'].shift(1)
    new_df['lag3'] = new_df['average_price'].shift(3)
    new_df['rolling_avg'] = new_df['average_price'].rolling(window=7).mean()
    new_df['days'] = (new_df.index - new_df.index.min()).total_seconds() // 86400
    new_df.dropna(inplace=True)
    return new_df
