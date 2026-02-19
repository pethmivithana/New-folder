import pickle
import json
import numpy as np
from pathlib import Path
import zipfile
import tempfile
import shutil
import warnings
warnings.filterwarnings('ignore')

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


class ModelLoader:
    def __init__(self, models_dir='ml_models'):
        self.models_dir = Path(models_dir)
        self.models   = {}
        self.artifacts = {}
        self.temp_dir  = None

    def load_all_models(self):
        if not self.models_dir.exists():
            print(f"✗ Models directory not found: {self.models_dir}")
            return False

        success = 0

        # ── 1. EFFORT MODELS (3 × XGBoost, 105 features each) ──────────────
        if XGBOOST_AVAILABLE:
            for variant in ['lower', 'median', 'upper']:
                path = self.models_dir / f'effort_model_{variant}.json'
                try:
                    m = xgb.Booster()
                    m.load_model(str(path))
                    self.models[f'effort_{variant}'] = m
                    success += 1
                    print(f"✓ effort_{variant}")
                except Exception as e:
                    print(f"✗ effort_{variant}: {e}")

        # ── 2. SCHEDULE RISK MODEL (XGBClassifier, 9 features) ───────────────
        path = self.models_dir / 'schedule_risk_model.pkl'
        try:
            with open(path, 'rb') as f:
                self.models['schedule_risk'] = pickle.load(f)
            success += 1
            print("✓ schedule_risk")
        except Exception as e:
            print(f"✗ schedule_risk: {e}")

        # ── 3. QUALITY RISK MODEL (TabNet, 6 features) ───────────────────────
        if TABNET_AVAILABLE and TORCH_AVAILABLE:
            zip_path    = self.models_dir / 'tabnet_quality_model.zip'
            params_path = self.models_dir / 'model_params.json'
            try:
                if zip_path.exists() and zipfile.is_zipfile(zip_path):
                    self.temp_dir = tempfile.mkdtemp()
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(self.temp_dir)

                    net_path = Path(self.temp_dir) / 'network.pt'
                    par_path = Path(self.temp_dir) / 'model_params.json'

                    if not par_path.exists() and params_path.exists():
                        import shutil as _sh
                        _sh.copy(params_path, par_path)

                    if par_path.exists() and net_path.exists():
                        with open(par_path) as f:
                            params = json.load(f)

                        model = TabNetClassifier(**params['init_params'])
                        state = torch.load(net_path, map_location='cpu')

                        # state can be an OrderedDict (weights) or the network object
                        if isinstance(state, dict):
                            model.network.load_state_dict(state)
                        else:
                            model.network = state

                        model.network.eval()
                        self.models['quality_risk'] = model
                        success += 1
                        print("✓ quality_risk")
            except Exception as e:
                print(f"✗ quality_risk: {e}")

        # ── 4. PRODUCTIVITY MODEL (XGBoost, 9 features) ──────────────────────
        if XGBOOST_AVAILABLE:
            path = self.models_dir / 'model_productivity_xgb.json'
            try:
                m = xgb.Booster()
                m.load_model(str(path))
                self.models['productivity'] = m
                success += 1
                print("✓ productivity")
            except Exception as e:
                print(f"✗ productivity: {e}")

        # ── 5. PRODUCTIVITY SCALER ────────────────────────────────────────────
        self._load_productivity_scaler()

        print(f"\nModels loaded: {success}/4")
        return success > 0

    def _load_productivity_scaler(self):
        """
        Load StandardScaler from productivity_artifacts.pkl.
        The pkl uses joblib internals; we parse mean_/scale_ directly
        from the binary rather than needing joblib to be installed.
        """
        path = self.models_dir / 'productivity_artifacts.pkl'
        if not path.exists():
            return

        try:
            # Try normal pickle first
            with open(path, 'rb') as f:
                obj = pickle.load(f)
            if hasattr(obj, 'mean_') and hasattr(obj, 'scale_'):
                from feature_engineering import feature_engineer
                feature_engineer.set_scaler(obj['scaler'].mean_, obj['scaler'].scale_)
                print("✓ productivity scaler loaded")
            elif isinstance(obj, dict) and 'scaler' in obj:
                sc = obj['scaler']
                from feature_engineering import feature_engineer
                feature_engineer.set_scaler(
                    np.array(sc.mean_),
                    np.array(sc.scale_)
                )
                print("✓ productivity scaler loaded")
        except Exception:
            # Scaler unavailable – predictions still work without it
            pass

    def cleanup(self):
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)


model_loader = ModelLoader()