"""
model_loader.py  — loads ALL 5 model files + 4 artifact files

Files consumed
--------------
ml_models/
  effort_model_lower.json          XGBoost Booster   105 features (reg:quantileerror)
  effort_model_median.json         XGBoost Booster   105 features
  effort_model_upper.json          XGBoost Booster   105 features
  schedule_risk_model.pkl          XGBClassifier     9 features  (multi:softprob, 4 classes)
  tabnet_quality_model.zip         TabNetClassifier  6 features  (binary)
  model_productivity_xgb.json      XGBoost Booster   9 features  (reg:squarederror)
  model_productivity_nn.pth        PyTorch MLP       9→64→32→1
  effort_artifacts.pkl             {tfidf, le_type}
  risk_artifacts.pkl               {imputer, le_type, le_prio, label_map, feature_names}
  productivity_artifacts.pkl       {scaler, le_type, le_prio, input_dim}
  le_prio_quality.pkl              LabelEncoder for quality priority
  model_params.json                TabNet init_params + class_attrs
"""

import io
import json
import pickle
import shutil
import warnings
import zipfile
import traceback
import sys
from pathlib import Path

import numpy as np

warnings.filterwarnings('ignore')

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from pytorch_tabnet.tab_model import TabNetClassifier
    TABNET_AVAILABLE = True
except ImportError:
    TABNET_AVAILABLE = False


def _joblib_load(path):
    """Load a pkl file preferring joblib, falling back to pickle."""
    if JOBLIB_AVAILABLE:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return joblib.load(path)
    with open(path, 'rb') as f:
        return pickle.load(f)


class ModelLoader:
    def __init__(self, models_dir='ml_models'):
        self.models_dir = Path(models_dir)
        self.models     = {}   # loaded model objects
        self.artifacts  = {}   # loaded artifact objects (tfidf, le_*, imputer, scaler)
        self._temp_dir  = None

    # ══════════════════════════════════════════════════════════════════════════
    def load_all_models(self) -> bool:
        if not self.models_dir.exists():
            print(f"✗ Models directory not found: {self.models_dir}")
            return False

        success = 0

        success += self._load_effort_models()
        success += self._load_schedule_risk()
        success += self._load_quality_risk()
        success += self._load_productivity()

        # Artifacts must be loaded AFTER models so label encoders are available
        self._load_effort_artifacts()
        self._load_risk_artifacts()
        self._load_productivity_artifacts()
        self._load_quality_artifacts()

        print(f"\nModels loaded: {success}/4")
        return success > 0

    # ── 1. Effort — 3 × XGBoost quantile regressors ──────────────────────────
    def _load_effort_models(self) -> int:
        if not XGBOOST_AVAILABLE:
            print("✗ effort_*: xgboost not installed")
            return 0
        loaded = 0
        for variant in ['lower', 'median', 'upper']:
            path = self.models_dir / f'effort_model_{variant}.json'
            try:
                m = xgb.Booster()
                m.load_model(str(path))
                self.models[f'effort_{variant}'] = m
                loaded += 1
                print(f"✓ effort_{variant}")
            except Exception as e:
                print(f"✗ effort_{variant}: {e}")
        # Count as 1 success if all three loaded
        return 1 if loaded == 3 else 0

    # ── 2. Schedule risk — XGBClassifier (multi:softprob, 4 classes) ─────────
    def _load_schedule_risk(self) -> int:
        path = self.models_dir / 'schedule_risk_model.pkl'
        try:
            self.models['schedule_risk'] = _joblib_load(path)
            print("✓ schedule_risk")
            return 1
        except Exception as e:
            print(f"✗ schedule_risk: {e}")
            return 0

    # ── 3. Quality risk — TabNet classifier (binary, 6 features) ─────────────
    def _load_quality_risk(self) -> int:
        if not (TABNET_AVAILABLE and TORCH_AVAILABLE):
            missing = []
            if not TABNET_AVAILABLE: missing.append('pytorch-tabnet')
            if not TORCH_AVAILABLE:  missing.append('torch')
            print(f"✗ quality_risk: {', '.join(missing)} not installed")
            return 0

        zip_path    = self.models_dir / 'tabnet_quality_model.zip'
        params_path = self.models_dir / 'model_params.json'

        if not zip_path.exists():
            print("✗ quality_risk: tabnet_quality_model.zip not found")
            return 0

        try:
            # ── Read model_params.json (from inside zip or alongside it) ──────
            saved = None
            with zipfile.ZipFile(zip_path) as zf:
                if 'model_params.json' in zf.namelist():
                    saved = json.loads(zf.read('model_params.json'))
            if saved is None and params_path.exists():
                saved = json.loads(params_path.read_text())
            if saved is None:
                raise FileNotFoundError("model_params.json not found")

            init_params = saved.get('init_params', {})
            class_attrs = saved.get('class_attrs', {})

            # ── Build TabNetClassifier and reconstruct its network ─────────────
            # TabNetClassifier() after __init__ is a bare Python shell.
            # .network (the nn.Module) does NOT exist until _set_network() is
            # called. Calling it here — BEFORE loading weights — is the fix.
            clf = TabNetClassifier(**init_params)
            for k, v in class_attrs.items():
                setattr(clf, k, v)
            clf._set_network()   # ← builds clf.network from the init_params

            # ── Load state_dict from network.pt inside the zip ────────────────
            with zipfile.ZipFile(zip_path) as zf:
                net_bytes = zf.read('network.pt')

            state_dict = torch.load(
                io.BytesIO(net_bytes),
                map_location='cpu',
                weights_only=True,
            )
            clf.network.load_state_dict(state_dict)
            clf.network.eval()

            self.models['quality_risk'] = clf
            print("✓ quality_risk")
            print(f"  [TabNet] Network structure: {clf.network}", file=sys.stderr)
            return 1

        except Exception as e:
            print(f"✗ quality_risk: {e}")
            print(f"  [ERROR DETAILS]", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return 0

    # ── 4. Productivity — XGBoost + MLP hybrid ────────────────────────────────
    def _load_productivity(self) -> int:
        loaded = 0

        # 4a. XGBoost component
        if XGBOOST_AVAILABLE:
            path = self.models_dir / 'model_productivity_xgb.json'
            try:
                m = xgb.Booster()
                m.load_model(str(path))
                self.models['productivity_xgb'] = m
                loaded += 1
                print("✓ productivity_xgb")
            except Exception as e:
                print(f"✗ productivity_xgb: {e}")

        # 4b. MLP neural network component
        # Architecture (from tensor shapes in model_productivity_nn.pth):
        #   Sequential(Linear(9,64), ReLU, Dropout, Linear(64,32), ReLU, Linear(32,1))
        if TORCH_AVAILABLE:
            path = self.models_dir / 'model_productivity_nn.pth'
            try:
                import torch.nn as nn

                class ProductivityMLP(nn.Module):
                    def __init__(self):
                        super().__init__()
                        self.model = nn.Sequential(
                            nn.Linear(9, 64),   # model.0  weight=576=64×9
                            nn.ReLU(),          # model.1
                            nn.Dropout(0.2),    # model.2
                            nn.Linear(64, 32),  # model.3  weight=2048=32×64
                            nn.ReLU(),          # model.4
                            nn.Linear(32, 1),   # model.5  weight=32=1×32
                        )
                    def forward(self, x):
                        return self.model(x)

                mlp = ProductivityMLP()
                state = torch.load(path, map_location='cpu', weights_only=True)
                mlp.load_state_dict(state)
                mlp.eval()
                self.models['productivity_nn'] = mlp
                loaded += 1
                print("✓ productivity_nn")
            except Exception as e:
                print(f"✗ productivity_nn: {e}")

        # Expose unified 'productivity' key pointing to XGBoost (primary model)
        if 'productivity_xgb' in self.models:
            self.models['productivity'] = self.models['productivity_xgb']

        return 1 if loaded > 0 else 0

    # ══════════════════════════════════════════════════════════════════════════
    # Artifact loaders — populate self.artifacts and push to feature_engineer
    # ══════════════════════════════════════════════════════════════════════════

    def _load_effort_artifacts(self):
        """Load effort_artifacts.pkl → {tfidf, le_type}"""
        path = self.models_dir / 'effort_artifacts.pkl'
        try:
            art = _joblib_load(path)
            self.artifacts['effort_tfidf']   = art['tfidf']
            self.artifacts['effort_le_type'] = art['le_type']

            # Push the real fitted vectorizer into feature_engineering
            from feature_engineering import set_tfidf_vectorizer, set_effort_le_type
            set_tfidf_vectorizer(art['tfidf'])
            set_effort_le_type(art['le_type'])
            print("✓ effort_artifacts (tfidf + le_type)")
        except Exception as e:
            print(f"✗ effort_artifacts: {e}")

    def _load_risk_artifacts(self):
        """Load risk_artifacts.pkl → {imputer, le_type, le_prio, label_map, feature_names}"""
        path = self.models_dir / 'risk_artifacts.pkl'
        try:
            art = _joblib_load(path)
            imputer = art['imputer']

            # ── sklearn version-compatibility patch ───────────────────────────
            # The imputer was saved with sklearn 1.6.1. In sklearn 1.8.0 the
            # internal attribute '_fill_dtype' was renamed to '_fit_dtype'.
            # Without this patch, imputer.transform() raises AttributeError.
            if not hasattr(imputer, '_fill_dtype') and hasattr(imputer, '_fit_dtype'):
                imputer._fill_dtype = imputer._fit_dtype

            self.artifacts['risk_imputer']  = imputer
            self.artifacts['risk_le_type']  = art['le_type']
            self.artifacts['risk_le_prio']  = art['le_prio']
            self.artifacts['risk_label_map']= art['label_map']

            from feature_engineering import set_risk_artifacts
            set_risk_artifacts(imputer, art['le_type'], art['le_prio'])
            print("✓ risk_artifacts (imputer + le_type + le_prio)")
        except Exception as e:
            print(f"✗ risk_artifacts: {e}")

    def _load_productivity_artifacts(self):
        """Load productivity_artifacts.pkl → {scaler, le_type, le_prio, input_dim}"""
        path = self.models_dir / 'productivity_artifacts.pkl'
        try:
            art = _joblib_load(path)
            self.artifacts['prod_scaler']  = art['scaler']
            self.artifacts['prod_le_type'] = art['le_type']
            self.artifacts['prod_le_prio'] = art['le_prio']

            from feature_engineering import set_productivity_artifacts
            set_productivity_artifacts(art['scaler'], art['le_type'], art['le_prio'])
            print("✓ productivity_artifacts (scaler + le_type + le_prio)")
        except Exception as e:
            print(f"✗ productivity_artifacts: {e}")

    def _load_quality_artifacts(self):
        """Load le_prio_quality.pkl → LabelEncoder for quality priority"""
        path = self.models_dir / 'le_prio_quality.pkl'
        try:
            le = _joblib_load(path)
            self.artifacts['quality_le_prio'] = le

            from feature_engineering import set_quality_artifacts
            set_quality_artifacts(le)
            print("✓ le_prio_quality")
        except Exception as e:
            print(f"✗ le_prio_quality: {e}")

    def cleanup(self):
        if self._temp_dir and Path(self._temp_dir).exists():
            shutil.rmtree(self._temp_dir)


model_loader = ModelLoader()
