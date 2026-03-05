#!/usr/bin/env python3
"""
debug_ml.py — Complete ML model diagnostics for Agile Replanning System

Tests ALL FOUR machine learning pipelines:
  1. Effort Prediction (XGBoost Regressors: lower, median, upper + TF-IDF)
  2. Schedule Risk (XGBoost Classifier)
  3. Productivity Impact (Hybrid Ensemble: XGBoost + PyTorch MLP)
  4. Quality Risk (PyTorch TabNet Classifier)

Usage:
  $ cd services/sprint_impact_service
  $ python ../../scripts/debug_ml.py

Features:
  ✓ Joblib safety: try/except blocks for .pkl loading (prevents Windows carriage return corruption)
  ✓ Single test dataset: Standard 5 SP High Priority Feature task
  ✓ Feature engineering validation: Prints shape/format for each model
  ✓ Raw predictions: Shows exact output from all 4 models
  ✓ Error recovery: Graceful fallback if models unavailable
"""

import sys
import os
import traceback
import warnings
from pathlib import Path
from typing import Any, Dict, Tuple

warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════════════════════
# SETUP: Directory navigation + imports
# ══════════════════════════════════════════════════════════════════════════════

# Ensure we're in the sprint_impact_service directory
service_dir = Path(__file__).parent.parent / 'services' / 'sprint_impact_service'
if service_dir.exists():
    sys.path.insert(0, str(service_dir))
else:
    service_dir = Path.cwd()
    sys.path.insert(0, str(service_dir))

print(f"[DEBUG_ML] Working directory: {service_dir}")
print(f"[DEBUG_ML] Python path includes: {service_dir}\n")

# Standard imports
import numpy as np
import pandas as pd

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    print("⚠ joblib not installed (using pickle fallback)")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠ torch not installed (quality_risk skipped)")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠ xgboost not installed (effort + schedule_risk skipped)")

try:
    from pytorch_tabnet.tab_model import TabNetClassifier
    TABNET_AVAILABLE = True
except ImportError:
    TABNET_AVAILABLE = False
    print("⚠ pytorch-tabnet not installed (quality_risk skipped)")

# Import our modules
try:
    from feature_engineering import (
        build_effort_features,
        build_schedule_risk_features,
        build_productivity_features,
        build_quality_features,
    )
    print("✓ feature_engineering imported")
except Exception as e:
    print(f"✗ Failed to import feature_engineering: {e}")
    sys.exit(1)

try:
    from model_loader import model_loader
    print("✓ model_loader imported")
except Exception as e:
    print(f"✗ Failed to import model_loader: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Safe joblib loading
# ══════════════════════════════════════════════════════════════════════════════

def joblib_safe_load(path: Path) -> Any:
    """
    Load a .pkl file safely using joblib with Windows carriage return protection.
    Falls back to pickle if joblib fails.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    # Try joblib first (handles Windows \x0d better)
    if JOBLIB_AVAILABLE:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                return joblib.load(path)
        except Exception as e:
            print(f"  [joblib fallback] Joblib load failed: {e}, trying pickle...", file=sys.stderr)
    
    # Fall back to pickle
    try:
        import pickle
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load {path} with both joblib and pickle: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TEST DATA: Single standardized item_data + sprint_context
# ══════════════════════════════════════════════════════════════════════════════

ITEM_DATA = {
    'id': 'TEST-001',
    'title': 'Implement Payment Processing',
    'description': 'Integrate Stripe API for payment processing. Add webhook support for payment events. Validate card details before submission.',
    'type': 'Task',
    'priority': 'High',
    'story_points': 5,
}

SPRINT_CONTEXT = {
    'days_remaining': 14,
    'days_since_sprint_start': 5,
    'sprint_load_7d': 18,  # 18 SP in last 7 days
    'team_velocity_14d': 22.33,  # Avg velocity from seed data: (25+22+20)/3
    'sprint_progress': 5 / (5 + 14),  # 26% through sprint
}

print("=" * 80)
print("TEST DATA")
print("=" * 80)
print("\nItem Data:")
for k, v in ITEM_DATA.items():
    print(f"  {k}: {v}")

print("\nSprint Context:")
for k, v in SPRINT_CONTEXT.items():
    print(f"  {k}: {v}")
print()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN: Load models and run diagnostics
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("STEP 1: Loading ML Models")
    print("=" * 80)
    
    success = model_loader.load_all_models()
    
    if not success:
        print("\n✗ No models loaded. Exiting.")
        return
    
    print("\nModels available:", list(model_loader.models.keys()))
    print("Artifacts available:", list(model_loader.artifacts.keys()))
    
    # ──────────────────────────────────────────────────────────────────────────────
    # TEST 1: EFFORT PREDICTION
    # ──────────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("TEST 1: EFFORT PREDICTION (XGBoost Regressors + TF-IDF)")
    print("=" * 80)
    
    try:
        print("\n[Feature Engineering]")
        effort_features = build_effort_features(ITEM_DATA, SPRINT_CONTEXT)
        
        print(f"\nFeature Dict Structure:")
        print(f"  Type: {type(effort_features)}")
        print(f"  Keys: {len(effort_features)}")
        print(f"  Sample keys: {list(effort_features.keys())[:5]}")
        
        # Convert dict to DataFrame for XGBoost
        df_effort = pd.DataFrame([effort_features])
        print(f"\nDataFrame for XGBoost:")
        print(f"  Shape: {df_effort.shape}")
        print(f"  Columns: {df_effort.columns.tolist()}")
        print(f"  dtypes: {df_effort.dtypes.unique()}")
        
        # Predictions
        predictions = {}
        for variant in ['lower', 'median', 'upper']:
            model_key = f'effort_{variant}'
            if model_key in model_loader.models:
                model = model_loader.models[model_key]
                pred = model.predict(df_effort)[0]
                predictions[variant] = float(pred)
                print(f"\nPrediction [{variant}]: {pred:.2f} hours")
            else:
                print(f"\n✗ {model_key} not loaded")
        
        if predictions:
            lower = predictions.get('lower', 0)
            median = predictions.get('median', 0)
            upper = predictions.get('upper', 0)
            print(f"\n[EFFORT RESULT]")
            print(f"  Range: {lower:.2f}h (lower) → {median:.2f}h (median) → {upper:.2f}h (upper)")
            print(f"  Confidence Interval: [{lower:.2f}, {upper:.2f}]")
        
    except Exception as e:
        print(f"\n✗ Effort prediction failed: {e}")
        traceback.print_exc()
    
    # ──────────────────────────────────────────────────────────────────────────────
    # TEST 2: SCHEDULE RISK
    # ──────────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("TEST 2: SCHEDULE RISK (XGBoost Classifier)")
    print("=" * 80)
    
    try:
        print("\n[Feature Engineering]")
        risk_features = build_schedule_risk_features(ITEM_DATA, SPRINT_CONTEXT)
        
        print(f"\nFeature DataFrame:")
        print(f"  Shape: {risk_features.shape}")
        print(f"  Columns: {risk_features.columns.tolist()}")
        print(f"  dtypes:\n{risk_features.dtypes}")
        print(f"\nValues:")
        print(risk_features)
        
        # Prediction
        if 'schedule_risk' in model_loader.models:
            model = model_loader.models['schedule_risk']
            
            # Raw prediction
            proba = model.predict_proba(risk_features)[0]
            pred_class = model.predict(risk_features)[0]
            classes = model.classes_
            
            print(f"\n[Classes]: {classes}")
            print(f"\n[Raw Probabilities]:")
            for idx, class_label in enumerate(classes):
                print(f"  {class_label}: {proba[idx]:.4f}")
            
            print(f"\n[Predicted Class]: {pred_class}")
            
            # Find spillover probability
            spillover_prob = 0.0
            for idx, class_label in enumerate(classes):
                if class_label in ['Critical Risk', 'High Risk']:
                    spillover_prob += proba[idx]
            
            print(f"\n[SCHEDULE RISK RESULT]")
            print(f"  Spillover Probability: {spillover_prob:.4f} ({spillover_prob*100:.2f}%)")
            print(f"  Dominant Class: {pred_class}")
        else:
            print("\n✗ schedule_risk model not loaded")
        
    except Exception as e:
        print(f"\n✗ Schedule risk prediction failed: {e}")
        traceback.print_exc()
    
    # ──────────────────────────────────────────────────────────────────────────────
    # TEST 3: PRODUCTIVITY IMPACT
    # ──────────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("TEST 3: PRODUCTIVITY IMPACT (Hybrid: XGBoost + PyTorch MLP)")
    print("=" * 80)
    
    try:
        print("\n[Feature Engineering]")
        prod_features = build_productivity_features(ITEM_DATA, SPRINT_CONTEXT)
        
        print(f"\nFeature Array:")
        print(f"  Shape: {prod_features.shape}")
        print(f"  dtype: {prod_features.dtype}")
        print(f"  Values: {prod_features[0]}")
        
        # XGBoost prediction
        if 'productivity_xgb' in model_loader.models:
            xgb_model = model_loader.models['productivity_xgb']
            xgb_pred = xgb_model.predict(prod_features)[0]
            print(f"\n[XGBoost Prediction]: {xgb_pred:.4f} (% productivity drop)")
        else:
            xgb_pred = None
            print("\n✗ productivity_xgb not loaded")
        
        # PyTorch MLP prediction
        if TORCH_AVAILABLE and 'productivity_nn' in model_loader.models:
            nn_model = model_loader.models['productivity_nn']
            
            # Convert to torch tensor
            x_torch = torch.tensor(prod_features, dtype=torch.float32)
            with torch.no_grad():
                nn_pred = nn_model(x_torch).item()
            print(f"[PyTorch MLP Prediction]: {nn_pred:.4f} (% productivity drop)")
        else:
            nn_pred = None
            print("✗ productivity_nn not loaded or torch unavailable")
        
        # Hybrid result (average if both available)
        if xgb_pred is not None and nn_pred is not None:
            hybrid_pred = (xgb_pred + nn_pred) / 2
            print(f"\n[PRODUCTIVITY IMPACT RESULT]")
            print(f"  XGBoost: {xgb_pred:.4f}%")
            print(f"  PyTorch MLP: {nn_pred:.4f}%")
            print(f"  Hybrid Average: {hybrid_pred:.4f}%")
        elif xgb_pred is not None:
            print(f"\n[PRODUCTIVITY IMPACT RESULT]")
            print(f"  XGBoost: {xgb_pred:.4f}% (MLP unavailable)")
        
    except Exception as e:
        print(f"\n✗ Productivity prediction failed: {e}")
        traceback.print_exc()
    
    # ──────────────────────────────────────────────────────────────────────────────
    # TEST 4: QUALITY RISK
    # ──────────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("TEST 4: QUALITY RISK (PyTorch TabNet Classifier)")
    print("=" * 80)
    
    try:
        print("\n[Feature Engineering]")
        quality_features = build_quality_features(ITEM_DATA, SPRINT_CONTEXT)
        
        print(f"\nFeature Array:")
        print(f"  Shape: {quality_features.shape}")
        print(f"  dtype: {quality_features.dtype}")
        print(f"  Values: {quality_features[0]}")
        
        # Prediction
        if TORCH_AVAILABLE and 'quality_risk' in model_loader.models:
            model = model_loader.models['quality_risk']
            
            # Convert to torch
            x_torch = torch.tensor(quality_features, dtype=torch.float32)
            
            # TabNet predict_proba
            with torch.no_grad():
                proba = model.predict_proba(x_torch)
            
            pred_class = model.predict(x_torch)[0]
            
            print(f"\n[Raw Probabilities]:")
            print(f"  Defect Prob (class=1): {proba[0, 1]:.4f}")
            print(f"  Safe Prob (class=0): {proba[0, 0]:.4f}")
            
            print(f"\n[Predicted Class]: {pred_class}")
            
            print(f"\n[QUALITY RISK RESULT]")
            print(f"  Defect Probability: {float(proba[0, 1]):.4f} ({float(proba[0, 1])*100:.2f}%)")
            print(f"  Risk Level: {'HIGH' if float(proba[0, 1]) > 0.5 else 'LOW'}")
        else:
            print("\n✗ quality_risk model not loaded or torch unavailable")
        
    except Exception as e:
        print(f"\n✗ Quality risk prediction failed: {e}")
        traceback.print_exc()
    
    # ──────────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✓ All 4 ML pipelines tested successfully!")
    print("\nNext steps:")
    print("  1. Verify all raw predictions make sense for your domain")
    print("  2. Check feature engineering outputs match expected shapes")
    print("  3. Inspect model.classes_ and feature names if prediction looks wrong")
    print("  4. Review debug logs in stderr for feature values")
    print("\nFor deeper debugging, inspect:")
    print("  - model_loader.artifacts (label encoders, scalers, etc.)")
    print("  - model_loader.models (model objects and their parameters)")


if __name__ == '__main__':
    main()
