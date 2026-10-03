"""
Scaler-aware feature clipping to prevent scaling explosion

This module clips feature values to be within reasonable bounds
relative to the trained scaler's statistics, preventing extreme
scaled values that cause model saturation.
"""

import pickle
import os

# Load the scaler once to get its statistics
_scaler_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'ethereum', 'scaler_augmented.pkl')
with open(_scaler_path, 'rb') as f:
    _SCALER = pickle.load(f)

# For each feature, compute reasonable bounds: mean ± 5*std
# Values beyond 5 standard deviations are extreme outliers
_FEATURE_BOUNDS = {}
for i, (mean, std) in enumerate(zip(_SCALER.mean_, _SCALER.scale_)):
    lower = mean - 5 * std
    upper = mean + 5 * std
    _FEATURE_BOUNDS[i] = (lower, upper)


def clip_features_for_scaler(features_dict):
    """
    Clip feature values to be within 5 standard deviations of training data
    
    This prevents scaling explosion when live data has extreme outliers.
    
    Args:
        features_dict: OrderedDict/dict with feature name -> value
    
    Returns:
        Clipped features_dict
    """
    feature_values = list(features_dict.values())
    feature_names = list(features_dict.keys())
    
    clipped_count = 0
    
    for i, (name, value) in enumerate(zip(feature_names, feature_values)):
        if i >= len(_FEATURE_BOUNDS):
            break
            
        lower, upper = _FEATURE_BOUNDS[i]
        
        if value < lower:
            # print(f"[CLIP] {name}: {value:.4f} -> {lower:.4f} (lower bound)")
            features_dict[name] = lower
            clipped_count += 1
        elif value > upper:
            # print(f"[CLIP] {name}: {value:.4f} -> {upper:.4f} (upper bound)")
            features_dict[name] = upper
            clipped_count += 1
    
    if clipped_count > 0:
        print(f"[INFO] Clipped {clipped_count} features to be within 5σ of training data")
    
    return features_dict
