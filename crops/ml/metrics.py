# crops/ml/metrics.py

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error, root_mean_squared_error

metrics_result = pd.DataFrame(columns=['model', 'mse', 'rmse', 'r2', 'mape', 'mad'])

def calc_metrics(actual, predictions, model, name="none", df=metrics_result):
    new_metrics = pd.DataFrame([{
        'model': name,
        'mse': mean_squared_error(actual, predictions),
        'rmse': root_mean_squared_error(actual, predictions),
        'r2': r2_score(actual, predictions),
        'mape': mean_absolute_percentage_error(actual, predictions),
        'mad': stats.median_abs_deviation(predictions, center=np.mean),
    }])
    merged_df = pd.concat([df, new_metrics], ignore_index=True)
    return merged_df
