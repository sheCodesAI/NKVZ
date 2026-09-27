"""
Bharat EntityGraph — Business Entity Resolution Platform
Model Wrapper Module
High-performance Gradient Boosted Decision Tree Matcher (MIT/Apache 2.0 License, <100K parameters).
"""

import os
from typing import List, Dict, Any, Tuple
import numpy as np
import joblib

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

from sklearn.ensemble import HistGradientBoostingClassifier

class BharatEntityMatcher:
    """Pairwise entity matching classifier optimized for precision-heavy F0.5."""
    
    def __init__(self, n_estimators: int = 350, learning_rate: float = 0.05, max_depth: int = 6, scale_pos_weight: float = 8.0):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.scale_pos_weight = scale_pos_weight
        self.model = None
        self.model_type = "lightgbm" if HAS_LGB else "hist_gbdt"
        
        if HAS_LGB:
            self.model = lgb.LGBMClassifier(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                num_leaves=31,
                min_child_samples=20,
                scale_pos_weight=self.scale_pos_weight,
                subsample=0.85,
                colsample_bytree=0.85,
                random_state=42,
                n_jobs=-1,
                verbosity=-1
            )
        else:
            self.model = HistGradientBoostingClassifier(
                max_iter=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                class_weight='balanced',
                min_samples_leaf=20,
                random_state=42
            )
            
    def fit(self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray = None):
        """Fits model with optional sample weighting."""
        if HAS_LGB and sample_weight is not None:
            self.model.fit(X, y, sample_weight=sample_weight)
        else:
            self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Returns match probabilities P(y=1)."""
        probs = self.model.predict_proba(X)
        return probs[:, 1]

    def save(self, filepath: str):
        """Serializes model to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> 'BharatEntityMatcher':
        """Loads serialized model."""
        return joblib.load(filepath)
