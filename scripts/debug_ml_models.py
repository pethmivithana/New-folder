#!/usr/bin/env python3
"""
Debug script to understand ML model structure and outputs.
Run this to diagnose issues with model predictions.
"""

import sys
import pickle
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'services' / 'sprint_impact_service'))

def debug_schedule_risk_model():
    """Inspect the schedule risk model structure."""
    print("\n" + "="*80)
    print("DEBUGGING: SCHEDULE RISK MODEL")
    print("="*80)
    
    model_path = Path('ml_models/schedule_risk_model.pkl')
    
    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        return
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f"\n✓ Model loaded successfully")
    print(f"  Type: {type(model).__name__}")
    print(f"  Model class: {model.__class__.__module__}.{model.__class__.__name__}")
    
    if hasattr(model, 'classes_'):
        classes = model.classes_
        print(f"\n📊 Classes ({len(classes)} total):")
        for idx, cls in enumerate(classes):
            print(f"    [{idx}] {repr(cls)} (type: {type(cls).__name__})")
    
    if hasattr(model, 'n_classes_'):
        print(f"\n  n_classes_: {model.n_classes_}")
    
    if hasattr(model, 'n_features_'):
        print(f"  n_features_: {model.n_features_}")
    
    print(f"\n  Other attributes:")
    for attr in dir(model):
        if not attr.startswith('_') and not callable(getattr(model, attr)):
            val = getattr(model, attr)
            if not isinstance(val, (list, dict, type(None))) or len(str(val)) < 100:
                print(f"    - {attr}: {repr(val)[:80]}")


def debug_risk_artifacts():
    """Inspect the risk artifacts (label encoders, imputer, etc)."""
    print("\n" + "="*80)
    print("DEBUGGING: RISK ARTIFACTS")
    print("="*80)
    
    artifacts_path = Path('ml_models/risk_artifacts.pkl')
    
    if not artifacts_path.exists():
        print(f"❌ Artifacts not found at {artifacts_path}")
        return
    
    with open(artifacts_path, 'rb') as f:
        artifacts = pickle.load(f)
    
    print(f"\n✓ Artifacts loaded successfully")
    print(f"  Keys: {list(artifacts.keys())}")
    
    if 'label_map' in artifacts:
        print(f"\n📋 Label Map:")
        label_map = artifacts['label_map']
        for idx, label in label_map.items():
            print(f"    [{idx}] {label}")
    
    if 'imputer' in artifacts:
        print(f"\n🔧 Imputer:")
        imputer = artifacts['imputer']
        print(f"    Type: {type(imputer).__name__}")
        if hasattr(imputer, 'statistics_'):
            print(f"    Statistics: {imputer.statistics_}")
    
    if 'le_type' in artifacts:
        print(f"\n🏷️  Type Label Encoder:")
        le = artifacts['le_type']
        print(f"    Type: {type(le).__name__}")
        if hasattr(le, 'classes_'):
            print(f"    Classes: {le.classes_}")
    
    if 'le_prio' in artifacts:
        print(f"\n🏷️  Priority Label Encoder:")
        le = artifacts['le_prio']
        print(f"    Type: {type(le).__name__}")
        if hasattr(le, 'classes_'):
            print(f"    Classes: {le.classes_}")


def debug_feature_engineering():
    """Test feature engineering with sample data."""
    print("\n" + "="*80)
    print("DEBUGGING: FEATURE ENGINEERING")
    print("="*80)
    
    try:
        from feature_engineering import build_schedule_risk_features
        from model_loader import model_loader
        
        # Load artifacts
        model_loader.load_all_models()
        
        # Create sample data
        item_data = {
            'description': 'A test task with some details and multiple http://links.com here',
            'story_points': 5,
            'priority': 'High',
            'type': 'Feature',
        }
        
        sprint_context = {
            'days_remaining': 7,
        }
        
        print(f"\n📝 Sample Item Data:")
        for k, v in item_data.items():
            print(f"    {k}: {v}")
        
        print(f"\n📊 Sprint Context:")
        for k, v in sprint_context.items():
            print(f"    {k}: {v}")
        
        # Build features
        X = build_schedule_risk_features(item_data, sprint_context)
        
        print(f"\n✓ Features built successfully")
        print(f"  Type: {type(X).__name__}")
        print(f"  Shape: {X.shape}")
        print(f"  Columns: {list(X.columns) if hasattr(X, 'columns') else 'N/A'}")
        print(f"  Values: {X.values if hasattr(X, 'values') else X}")
        
        # Make prediction
        if 'schedule_risk' in model_loader.models:
            model = model_loader.models['schedule_risk']
            proba = model.predict_proba(X)[0]
            
            print(f"\n🎯 Predictions:")
            print(f"  Probabilities: {proba}")
            print(f"  Sum: {proba.sum()}")
            
            classes = model.classes_
            print(f"  Classes: {classes}")
            
            for idx, (cls, prob) in enumerate(zip(classes, proba)):
                print(f"    [{idx}] {cls}: {prob:.4f} ({prob*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error during feature engineering: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_schedule_risk_model()
    debug_risk_artifacts()
    debug_feature_engineering()
    print("\n" + "="*80)
    print("✓ Debugging complete")
    print("="*80 + "\n")
