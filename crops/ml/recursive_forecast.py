# crops/ml/recursive_forecast.py

import numpy as np
import pandas as pd

def recursive_forecast(df, model, forecast_days=90):
    future_dates = pd.date_range(df.index.max() + pd.Timedelta(days=1), periods=forecast_days)
    future_prices = []
    last_known = df.iloc[-1]
    
    for day in range(1, forecast_days + 1):
        future_day = last_known['days'] + day
        price_lag_1 = last_known['average_price']
        if future_day - 3 in df['days'].values:
            price_lag_3 = df.loc[df['days'] == (future_day - 3), 'average_price'].iloc[-1]
        else:
            price_lag_3 = price_lag_1
        rolling_mean_7 = np.mean([price_lag_1] + future_prices[-6:])

        features = pd.DataFrame([[price_lag_1, price_lag_3, rolling_mean_7]], 
                        columns=["lag1", "lag3", "rolling_avg"])
        predicted_price = model.predict(features)[0]
        future_prices.append(predicted_price)
        
        last_known = pd.Series({'days': future_day, 'average_price': predicted_price})
    
    result = pd.DataFrame({'date': future_dates, 'predicted_price': future_prices})
    result.set_index('date', inplace=True)
    return result
