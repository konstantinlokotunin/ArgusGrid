"""
feature_engineering.py
Vektorisiertes Feature-Preprocessing für das TensorFlow AutoEncoder-Modell.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

class CompactFeaturePipeline:
    """Transforms raw time series into normalized, cyclically encoded ML feature matrices."""
    
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def fit_transform(self, df: pd.DataFrame, target_cols: list) -> pd.DataFrame:
        """Computes cycles, trains the feature scaler, and scales the matrix."""
        # Cyclical transformation via vectorised numpy math
        hours = df.index.hour
        df["sin_hour"] = np.sin(2 * np.pi * hours / 24.0)
        df["cos_hour"] = np.cos(2 * np.pi * hours / 24.0)
        
        feature_columns = target_cols + ["sin_hour", "cos_hour"]
        
        # Scaling directly to a clean dataframe output
        scaled_array = self.scaler.fit_transform(df[feature_columns])
        return pd.DataFrame(scaled_array, index=df.index, columns=feature_columns)