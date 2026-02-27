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
        self.models     = {}
        self.artifacts  = {}
        self.temp_dir   = None

    def load_all_models(self):
        if not self.models_dir.exists():
            print(f"✗ Models directory not found: {self.models_dir}")
            return False

        success = 0

        # ── 1. EFFORT MODELS (3 × XGBoost) ───────────────────────────────────
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

        # ── 2. SCHEDULE RISK MODEL (XGBClassifier) ────────────────────────────
        path = self.models_dir / 'schedule_risk_model.pkl'
        try:
            with open(path, 'rb') as f:
                self.models['schedule_risk'] = pickle.load(f)
            success += 1
            print("✓ schedule_risk")
        except Exception as e:
            print(f"✗ schedule_risk: {e}")

        # ── 3. QUALITY RISK MODEL (TabNet) ────────────────────────────────────
        if TABNET_AVAILABLE and TORCH_AVAILABLE:
            zip_path    = self.models_dir / 'tabnet_quality_model.zip'
            params_path = self.models_dir / 'model_params.json'

            if not zip_path.exists():
                print("✗ quality_risk: tabnet_quality_model.zip not found")
            else:
                try:
                    self._load_tabnet(zip_path, params_path)
                    success += 1
                except Exception as e:
                    print(f"✗ quality_risk: {e}")
                    print("  quality_risk will use the heuristic fallback (40% defect estimate)")

        elif not TABNET_AVAILABLE:
            print("✗ quality_risk: pytorch-tabnet not installed → pip install pytorch-tabnet")
        elif not TORCH_AVAILABLE:
            print("✗ quality_risk: torch not installed → pip install torch")

        # ── 4. PRODUCTIVITY MODEL (XGBoost) ───────────────────────────────────
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

    def _load_tabnet(self, zip_path: Path, params_path: Path):
        """
        Load TabNetClassifier from the zip produced by pytorch-tabnet's .save_model().
        """
        # ── Step 1: read params ───────────────────────────────────────────────
        saved = None
        with zipfile.ZipFile(zip_path, 'r') as zf:
            if 'model_params.json' in zf.namelist():
                saved = json.loads(zf.read('model_params.json'))

        # Fall back to the standalone params file next to the zip
        if saved is None and params_path.exists():
            with open(params_path) as f:
                saved = json.load(f)

        if saved is None:
            raise FileNotFoundError(
                "model_params.json not found inside tabnet_quality_model.zip "
                f"or at {params_path}"
            )

        init_params  = saved.get('init_params', {})
        class_attrs  = saved.get('class_attrs', {})

        # ── Step 2: create bare TabNetClassifier ─────────────────────────────
        clf = TabNetClassifier(**init_params)

        for k, v in class_attrs.items():
            setattr(clf, k, v)

        # ── Step 3: build the nn.Module — THE MISSING STEP ───────────────────
        clf._set_network()

        # ── Step 4: load the state_dict into the now-existing network ─────────
        with zipfile.ZipFile(zip_path, 'r') as zf:
            net_bytes = zf.read('network.pt')

        import io
        state_dict = torch.load(
            io.BytesIO(net_bytes),
            map_location='cpu',
            weights_only=True,   # safe: we confirmed it's an OrderedDict
        )

        clf.network.load_state_dict(state_dict)

        # ── Step 5: switch to inference mode ──────────────────────────────────
        clf.network.eval()

        self.models['quality_risk'] = clf
        print("✓ quality_risk")

    def _load_productivity_scaler(self):
        path = self.models_dir / 'productivity_artifacts.pkl'
        if not path.exists():
            return
        try:
            with open(path, 'rb') as f:
                obj = pickle.load(f)
            if hasattr(obj, 'mean_') and hasattr(obj, 'scale_'):
                from feature_engineering import feature_engineer
                feature_engineer.set_scaler(np.array(obj.mean_), np.array(obj.scale_))
                print("✓ productivity scaler loaded")
            elif isinstance(obj, dict) and 'scaler' in obj:
                sc = obj['scaler']
                from feature_engineering import feature_engineer
                feature_engineer.set_scaler(np.array(sc.mean_), np.array(sc.scale_))
                print("✓ productivity scaler loaded")
        except Exception:
            pass  # predictions still work without scaler

    def cleanup(self):
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)


model_loader = ModelLoader()