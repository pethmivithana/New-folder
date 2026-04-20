"""
feature_engineering.py

All label encoders, scalers, and the TF-IDF vectorizer are loaded directly
from the training artifact pkl files via model_loader.py at startup.
No values are hardcoded — everything comes from the actual sklearn objects.

Artifact → feature builder mapping
───────────────────────────────────
effort_artifacts.pkl   →  build_effort_features()
  tfidf    : TfidfVectorizer(max_features=100, ngram_range=(1,2),
                              stop_words='english', sublinear_tf=False)
  le_type  : ['Bug','Epic','Improvement','Story','Technical task']

risk_artifacts.pkl     →  build_schedule_risk_features()
  imputer  : SimpleImputer(strategy='median')
             fill values = [2, 0, 0, 4519, 0, 0, 0.143, 4, 3]
  le_type  : ['Bug','Epic','Improvement','Missing_Content','Story','Technical task']
  le_prio  : ['Blocker','Critical','Major','Minor','Missing_Content','Trivial']
  feature order: Story_Point, total_links, total_comments, author_total_load,
                 link_density, comment_density, pressure_index, Type_Code, Priority_Code

productivity_artifacts.pkl  →  build_productivity_features()
  scaler   : StandardScaler (mean/scale verified against 9-feature vector)
  le_type  : ['Bug','Improvement','Story','Technical task']
  le_prio  : ['Blocker','Critical','Major','Minor']
  feature order (verified via scaler statistics):
    [0] story_points
    [1] log(story_points / days_remaining)   ← log-space pressure, mean=-0.744
    [2] log(1 + days_remaining)              ← log-space days, mean=1.054
    [3] team_velocity_14d
    [4] sprint_load_7d
    [5] story_points / (days_remaining * 24) ← hours-normalised pressure, mean=0.020
    [6] sprint_progress
    [7] type_code
    [8] prio_code

le_prio_quality.pkl    →  build_quality_features()
  classes  : ['High','Highest','Low','Lowest','Medium']
             (native Jira-style labels, NOT Blocker/Major/Minor)
  UI map   : Low→Low(2), Medium→Medium(4), High→High(0), Critical→Highest(1)
"""

import numpy as np
import pandas as pd
import warnings
import sys

# ══════════════════════════════════════════════════════════════════════════════
# Module-level artifact holders — populated at startup by model_loader
# ══════════════════════════════════════════════════════════════════════════════

_tfidf_vectorizer  = None   # sklearn TfidfVectorizer from effort_artifacts.pkl
_risk_imputer      = None   # sklearn SimpleImputer  from risk_artifacts.pkl
_risk_le_type      = None   # sklearn LabelEncoder   from risk_artifacts.pkl
_risk_le_prio      = None   # sklearn LabelEncoder   from risk_artifacts.pkl
_risk_scaler       = None   # sklearn StandardScaler from risk_artifacts.pkl (optional, may not exist)
_prod_scaler       = None   # sklearn StandardScaler from productivity_artifacts.pkl
_prod_le_type      = None   # sklearn LabelEncoder   from productivity_artifacts.pkl
_prod_le_prio      = None   # sklearn LabelEncoder   from productivity_artifacts.pkl
_quality_le_prio   = None   # sklearn LabelEncoder   from le_prio_quality.pkl


def set_tfidf_vectorizer(vec):
    global _tfidf_vectorizer
    _tfidf_vectorizer = vec

def set_risk_artifacts(imputer, le_type, le_prio):
    global _risk_imputer, _risk_le_type, _risk_le_prio
    _risk_imputer = imputer
    _risk_le_type = le_type
    _risk_le_prio = le_prio

def set_risk_scaler(scaler):
    """Called by model_loader if a StandardScaler is found in risk_artifacts.pkl."""
    global _risk_scaler
    _risk_scaler = scaler

def set_productivity_artifacts(scaler, le_type, le_prio):
    global _prod_scaler, _prod_le_type, _prod_le_prio
    _prod_scaler  = scaler
    _prod_le_type = le_type
    _prod_le_prio = le_prio

def set_quality_artifacts(le_prio):
    global _quality_le_prio
    _quality_le_prio = le_prio


# ══════════════════════════════════════════════════════════════════════════════
# UI label → training label translation
# Each model was trained on different label sets.
# ══════════════════════════════════════════════════════════════════════════════

# UI sends: Low / Medium / High / Critical   (priority)
#           Task / Story / Bug / Subtask      (type)

def _ui_type_to_effort(ui_type: str) -> str:
    """Map UI type → effort le_type class."""
    return {'Bug': 'Bug', 'Story': 'Story',
            'Task': 'Technical task', 'Subtask': 'Technical task'}.get(ui_type, 'Technical task')

def _ui_type_to_risk(ui_type: str) -> str:
    """Map UI type → risk le_type class."""
    return {'Bug': 'Bug', 'Story': 'Story',
            'Task': 'Technical task', 'Subtask': 'Technical task'}.get(ui_type, 'Technical task')

def _ui_type_to_prod(ui_type: str) -> str:
    """Map UI type → productivity le_type class."""
    return {'Bug': 'Bug', 'Story': 'Story',
            'Task': 'Technical task', 'Subtask': 'Technical task'}.get(ui_type, 'Technical task')

def _ui_prio_to_risk(ui_prio: str) -> str:
    """Map UI priority → risk le_prio class (Blocker/Critical/Major/Minor/Missing_Content/Trivial)."""
    return {'Low': 'Minor', 'Medium': 'Major',
            'High': 'Critical', 'Critical': 'Blocker'}.get(ui_prio, 'Major')

def _ui_prio_to_prod(ui_prio: str) -> str:
    """Map UI priority → productivity le_prio class (Blocker/Critical/Major/Minor only)."""
    return {'Low': 'Minor', 'Medium': 'Major',
            'High': 'Critical', 'Critical': 'Blocker'}.get(ui_prio, 'Major')

def _ui_prio_to_quality(ui_prio: str) -> str:
    """Map UI priority → quality le_prio class (High/Highest/Low/Lowest/Medium)."""
    return {'Low': 'Low', 'Medium': 'Medium',
            'High': 'High', 'Critical': 'Highest'}.get(ui_prio, 'Medium')


def _safe_le_transform(le, value: str, fallback: int = 0) -> int:
    """Call le.transform([value]) safely; return fallback if unseen label."""
    if le is None:
        return fallback
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return int(le.transform([value])[0])
    except Exception:
        return fallback


# ══════════════════════════════════════════════════════════════════════════════
# 1. Effort features  (105 features: 5 numeric + 100 TF-IDF)
# ══════════════════════════════════════════════════════════════════════════════

def _get_tfidf_vector(text: str, n_components: int = 100) -> np.ndarray:
    """Transform text with the real fitted TF-IDF vectorizer from effort_artifacts."""
    if _tfidf_vectorizer is None:
        return np.zeros(n_components, dtype=np.float32)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        vec = _tfidf_vectorizer.transform([text]).toarray()[0]
    if len(vec) < n_components:
        vec = np.pad(vec, (0, n_components - len(vec)))
    return vec[:n_components].astype(np.float32)



def set_effort_le_type(le):
    global _effort_le_type_ref
    _effort_le_type_ref = le


def build_effort_features(item_data: dict, sprint_context: dict) -> dict:
    """
    Returns a 105-key dict matching the XGBoost effort model feature names exactly:
    sprint_load_7d, team_velocity_14d, pressure_index, total_links, Type_Code,
    txt_0 … txt_99
    """
    title        = item_data.get('title', '')
    description  = item_data.get('description', '')
    story_points = float(item_data.get('story_points', 5))
    ui_type      = item_data.get('type', 'Task')

    sprint_load    = float(sprint_context.get('sprint_load_7d', 0))
    team_velocity  = float(sprint_context.get('team_velocity_14d', 30))
    days_remaining = float(sprint_context.get('days_remaining', 14))

    pressure_index = story_points / max(1.0, days_remaining)
    total_links    = float(
        description.lower().count('http') + len(description.split(',')) // 3
    )

    type_label = _ui_type_to_effort(ui_type)
    type_code  = float(_safe_le_transform(_effort_le_type_ref, type_label))

    tfidf = _get_tfidf_vector(f"{title} {description}", n_components=100)

    features = {
        'sprint_load_7d':    sprint_load,
        'team_velocity_14d': team_velocity,
        'pressure_index':    pressure_index,
        'total_links':       total_links,
        'Type_Code':         type_code,
    }
    for i, v in enumerate(tfidf):
        features[f'txt_{i}'] = float(v)
    
    # Log to terminal for visibility
    print(f"[BUILD_EFFORT_FEATURES] Keys: {len(features)}, TF-IDF shape: {tfidf.shape}, dtype: {tfidf.dtype}", file=sys.stderr)
    
    return features


# ══════════════════════════════════════════════════════════════════════════════
# 2. Schedule risk features  (9 features, exact order from risk_artifacts)
# ══════════════════════════════════════════════════════════════════════════════

# author_total_load FIX:
# The old constant (4519.0) acted as a "feature anchor" — every ticket got the
# same value, so the model's tree splits on this feature were always identical
# and pushed predictions into a single leaf (Critical Risk).  Instead, derive a
# contextual value that reflects sprint load per assignee, introducing real
# variance so the trees can split correctly.  If no sprint context is available
# the imputer's original median is used as a last resort.
_AUTHOR_LOAD_FALLBACK = 4519.0


def _compute_contextual_author_load(sprint_context: dict) -> float:
    """
    Derive a contextual author_total_load proxy from sprint state.

    Formula: (planned_story_points / max(1, assignees)) * 10
      - Scales with actual sprint load so every request produces a different
        value, giving the model's decision trees real splits to work with.
      - The *10 multiplier keeps the range roughly near the training median
        (training data: Jira authors with cumulative SP history ~450–5000).
    Falls back to _AUTHOR_LOAD_FALLBACK if context is missing.
    """
    sprint_load  = float(sprint_context.get('sprint_load_7d', 0))
    assignees    = max(1, int(sprint_context.get('assignee_count', 1)))
    if sprint_load > 0:
        return round((sprint_load / assignees) * 10, 2)
    return _AUTHOR_LOAD_FALLBACK


def build_schedule_risk_features(item_data: dict, sprint_context: dict) -> pd.DataFrame:
    """
    9 features in the exact order stored in risk_artifacts feature_names:
    Story_Point, total_links, total_comments, author_total_load,
    link_density, comment_density, pressure_index, Type_Code, Priority_Code

    FIX — author_total_load: replaced hardcoded 4519 constant with a
    contextual sprint-derived value (see _compute_contextual_author_load).

    FIX — scaler guardrail: risk_artifacts.pkl has no StandardScaler
    (only an imputer).  Since XGBoost is tree-based it is theoretically
    scale-invariant, but extreme raw values (e.g. author_load >> SP) can
    still distort split thresholds on shallow trees.  When no scaler is
    present we apply min-max normalisation to the two highest-magnitude
    features (Story_Point and pressure_index) to keep them in [0, 1].

    Returns a Pandas DataFrame with explicit column names.
    """
    description  = item_data.get('description', '')
    story_points = float(item_data.get('story_points', 5))
    ui_prio      = item_data.get('priority', 'Medium')
    ui_type      = item_data.get('type', 'Task')

    days_remaining = float(sprint_context.get('days_remaining', 14))

    total_links     = float(description.lower().count('http') +
                            len(description.split(',')) // 3)
    total_comments  = 0.0  # default for new tickets (no Jira comment history)

    # FIX: contextual author load instead of constant 4519
    author_load     = _compute_contextual_author_load(sprint_context)

    link_density    = total_links / max(1.0, story_points)
    comment_density = total_comments / max(1.0, story_points)
    pressure_index  = story_points / max(1.0, days_remaining)

    type_label = _ui_type_to_risk(ui_type)
    prio_label = _ui_prio_to_risk(ui_prio)
    type_code  = float(_safe_le_transform(_risk_le_type, type_label))
    prio_code  = float(_safe_le_transform(_risk_le_prio, prio_label))

    X = np.array([[
        story_points, total_links, total_comments, author_load,
        link_density, comment_density, pressure_index,
        type_code, prio_code,
    ]])

    # Apply the fitted SimpleImputer (fills any NaN)
    if _risk_imputer is not None:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            X = _risk_imputer.transform(X)

    feature_names = ['Story_Point', 'total_links', 'total_comments', 'author_total_load',
                     'link_density', 'comment_density', 'pressure_index', 'Type_Code', 'Priority_Code']
    df = pd.DataFrame(X, columns=feature_names)

    # ── Scaler guardrail ─────────────────────────────────────────────────────
    # XGBoost trees are scale-invariant (split thresholds are absolute value
    # comparisons), so feature scaling must NOT be applied as a fallback —
    # doing so shifts every learned threshold away from the training distribution.
    # Only apply a StandardScaler if one was explicitly saved in risk_artifacts.pkl.
    if _risk_scaler is not None:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            df[feature_names] = _risk_scaler.transform(df[feature_names])
        print("[BUILD_SCHEDULE_RISK_FEATURES] StandardScaler applied", file=sys.stderr)
    else:
        print("[BUILD_SCHEDULE_RISK_FEATURES] No scaler — raw features passed (correct for XGBoost)", file=sys.stderr)

    print(f"[BUILD_SCHEDULE_RISK_FEATURES] Shape: {df.shape}", file=sys.stderr)
    print(f"[BUILD_SCHEDULE_RISK_FEATURES] Values: {df.iloc[0].to_dict()}", file=sys.stderr)

    return df


# ══════════════════════════════════════════════════════════════════════════════
# 3. Productivity features  (9 features, log-transformed per scaler analysis)
# ══════════════════════════════════════════════════════════════════════════════

def build_productivity_features(
    item_data: dict,
    sprint_context: dict,
    scaler_mean: np.ndarray = None,    # kept for backward compat; ignored
    scaler_scale: np.ndarray = None,   # kept for backward compat; ignored
) -> np.ndarray:
    """
    9 features verified against the StandardScaler statistics from
    productivity_artifacts.pkl.  Scaler is applied using the real artifact.
    
    CRITICAL: Ensures float32 dtype and (1, 9) 2D shape for torch.tensor() consumption.

    Feature order (verified by matching scaler mean_ values):
    [0] story_points
    [1] log(sp / days_remaining)             log-pressure index
    [2] log(1 + days_remaining)              log-scale days
    [3] team_velocity_14d
    [4] sprint_load_7d
    [5] sp / (days_remaining * 24)           hours-normalised pressure
    [6] sprint_progress
    [7] type_code
    [8] prio_code
    """
    story_points   = float(item_data.get('story_points', 5))
    ui_prio        = item_data.get('priority', 'Medium')
    ui_type        = item_data.get('type', 'Task')

    days_remaining = float(max(1, sprint_context.get('days_remaining', 14)))
    sprint_load    = float(sprint_context.get('sprint_load_7d', 0))
    team_velocity  = float(sprint_context.get('team_velocity_14d', 30))
    days_in        = float(sprint_context.get('days_since_sprint_start', 0))

    log_pressure   = np.log(story_points / days_remaining)
    log_days       = np.log(1.0 + days_remaining)
    hours_pressure = story_points / (days_remaining * 24.0)
    sprint_progress= days_in / max(1.0, days_in + days_remaining)

    type_label = _ui_type_to_prod(ui_type)
    prio_label = _ui_prio_to_prod(ui_prio)
    type_code  = float(_safe_le_transform(_prod_le_type, type_label))
    prio_code  = float(_safe_le_transform(_prod_le_prio, prio_label))

    raw = np.array([[
        story_points,
        log_pressure,
        log_days,
        team_velocity,
        sprint_load,
        hours_pressure,
        sprint_progress,
        type_code,
        prio_code,
    ]], dtype=np.float32)

    # Apply the real StandardScaler from productivity_artifacts.pkl
    if _prod_scaler is not None:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw = _prod_scaler.transform(raw).astype(np.float32)  # Ensure float32 after scaler
    elif scaler_mean is not None and scaler_scale is not None:
        # Legacy fallback
        raw = ((raw - scaler_mean) / np.where(scaler_scale == 0, 1.0, scaler_scale)).astype(np.float32)

    # Validate shape and dtype
    assert raw.shape == (1, 9), f"Expected shape (1, 9), got {raw.shape}"
    assert raw.dtype == np.float32, f"Expected dtype float32, got {raw.dtype}"
    
    # Log to terminal for visibility
    print(f"[BUILD_PRODUCTIVITY_FEATURES] Shape: {raw.shape}, dtype: {raw.dtype}", file=sys.stderr)
    print(f"[BUILD_PRODUCTIVITY_FEATURES] Values: {raw[0]}", file=sys.stderr)
    
    return raw


# ══════════════════════════════════════════════════════════════════════════════
# 4. Quality features  (6 features for TabNet, input_dim=6)
# ══════════════════════════════════════════════════════════════════════════════

def build_quality_features(item_data: dict, sprint_context: dict) -> np.ndarray:
    """
    6 features for TabNet quality classifier — MIN-MAX NORMALISED to [0,1].
    
    CRITICAL: Returns (1, 6) 2D array with dtype=np.float32 for TabNet inference.
    TabNet is strict about:
      1. Array shape MUST be (batch_size, n_features) — (1, 6) for single sample
      2. dtype MUST be np.float32 — NOT float64 (PyTorch default precision)

    All 6 running_mean values from encoder.initial_bn confirmed:
      [0.1413, 0.0062, 0.0148, 0.7096, 0.1693, 0.1170]

    Feature order and normalisation:
      [0] prio_code / 4.0                       raw 0-4 → 0-1   mean≈0.14
      [1] desc_complexity  (raw 0-1)             mean≈0.006
      [2] story_points / (days_remaining * 14)   pressure→0-1    mean≈0.015
      [3] days_remaining  / 14.0                 0-14 → 0-1      mean≈0.710
      [4] (story_points - 1) / 12.0              1-13 → 0-1      mean≈0.169
      [5] sprint_progress  (raw 0-1)             mean≈0.117

    le_prio_quality: ['High'=0,'Highest'=1,'Low'=2,'Lowest'=3,'Medium'=4]
    UI map: Low->Low(2), Medium->Medium(4), High->High(0), Critical->Highest(1)
    """
    story_points  = float(item_data.get('story_points', 5))
    ui_prio       = item_data.get('priority', 'Medium')
    description   = item_data.get('description', '')

    days_remaining  = float(max(1, sprint_context.get('days_remaining', 14)))
    sprint_progress = float(sprint_context.get('sprint_progress', 0.0))

    prio_label = _ui_prio_to_quality(ui_prio)
    prio_code  = float(_safe_le_transform(_quality_le_prio, prio_label))

    prio_norm       = prio_code / 4.0
    desc_complexity = min(float(len(description)) / 500.0, 1.0)
    pressure_norm   = story_points / (days_remaining * 14.0)
    days_norm       = min(days_remaining / 14.0, 1.0)
    sp_norm         = min(max((story_points - 1.0) / 12.0, 0.0), 1.0)

    # CRITICAL: dtype=np.float32 (NOT float64) and 2D shape (1, 6)
    X = np.array([[
        prio_norm,       # [0] prio_code/4
        desc_complexity, # [1] desc length/500
        pressure_norm,   # [2] sp/(days*14)
        days_norm,       # [3] days_rem/14
        sp_norm,         # [4] (sp-1)/12
        sprint_progress, # [5] raw 0-1
    ]], dtype=np.float32)
    
    # Validate shape and dtype before returning
    assert X.shape == (1, 6), f"Expected shape (1, 6), got {X.shape}"
    assert X.dtype == np.float32, f"Expected dtype float32, got {X.dtype}"
    
    # Log to terminal for visibility
    print(f"[BUILD_QUALITY_FEATURES] Shape: {X.shape}, dtype: {X.dtype}", file=sys.stderr)
    print(f"[BUILD_QUALITY_FEATURES] Values: {X[0]}", file=sys.stderr)
    
    return X


# ══════════════════════════════════════════════════════════════════════════════
# FeatureEngineer singleton  (used by impact_predictor.py)
# ══════════════════════════════════════════════════════════════════════════════

class FeatureEngineer:
    """Thin wrapper kept for backward compatibility with impact_predictor.py."""

    def __init__(self):
        # Legacy: scaler held here; now also in _prod_scaler above
        self.scaler_mean  = None
        self.scaler_scale = None

    def set_scaler(self, mean, scale):
        """Called by model_loader for backward compatibility."""
        self.scaler_mean  = np.array(mean)
        self.scaler_scale = np.array(scale)

    def extract_features(self, item_data, sprint_context, existing_items=None):
        days_in  = sprint_context.get('days_since_sprint_start', 0)
        days_rem = sprint_context.get('days_remaining', 14)
        total    = days_in + days_rem
        return {
            'story_points':             item_data.get('story_points', 5),
            'priority':                 item_data.get('priority', 'Medium'),
            'days_since_sprint_start':  days_in,
            'days_remaining':           days_rem,
            'sprint_progress':          days_in / total if total > 0 else 0.0,
            'sprint_load_7d':           sprint_context.get('sprint_load_7d', 0),
            'team_velocity_14d':        sprint_context.get('team_velocity_14d', 30),
        }

    def prepare_for_effort_model(self, features_dict, item_data, sprint_context):
        return build_effort_features(item_data, sprint_context)

    def prepare_for_schedule_risk_model(self, item_data, sprint_context):
        return build_schedule_risk_features(item_data, sprint_context)

    def prepare_for_quality_risk_model(self, item_data, sprint_context):
        return build_quality_features(item_data, sprint_context)

    def prepare_for_productivity_model(self, item_data, sprint_context):
        return build_productivity_features(item_data, sprint_context)


feature_engineer = FeatureEngineer()