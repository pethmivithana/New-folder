import numpy as np
import joblib
import os
from datetime import datetime

# ── Real TF-IDF vectorizer (exported from Jupyter notebook) ──────────────────
_VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "tfidf_vectorizer.pkl")
_tfidf_vectorizer = None

try:
    _tfidf_vectorizer = joblib.load(_VECTORIZER_PATH)
    print(f"  ✅  TF-IDF vectorizer loaded from {_VECTORIZER_PATH}")
except FileNotFoundError:
    print(f"  ⚠️  tfidf_vectorizer.pkl not found at {_VECTORIZER_PATH}. "
          "Effort text features will be zeros until the file is present.")
except Exception as e:
    print(f"  ⚠️  Failed to load TF-IDF vectorizer: {e}. "
          "Effort text features will be zeros.")


def _get_tfidf_vector(text: str, n_components: int = 100) -> np.ndarray:
    if _tfidf_vectorizer is None:
        return np.zeros(n_components, dtype=np.float32)
    vec = _tfidf_vectorizer.transform([text]).toarray()[0]
    # Pad or truncate to exactly n_components to match what the model expects
    if len(vec) < n_components:
        vec = np.pad(vec, (0, n_components - len(vec)), constant_values=0.0)
    elif len(vec) > n_components:
        vec = vec[:n_components]
    return vec.astype(np.float32)


# ── Label encoders (must match training artifacts) ────────────────────────────
TYPE_CLASSES      = ['Epic', 'Improvement', 'Missing_Content', 'Story', 'Technical task']
PRIO_CLASSES_RISK = ['Blocker', 'Critical', 'Major', 'Minor', 'Missing_Content', 'Trivial']
PRIO_CLASSES_PROD = ['Blocker', 'Critical', 'Major', 'Minor', 'Missing_Content', 'Trivial']

PRIORITY_MAP = {
    'Low':      'Minor',
    'Medium':   'Major',
    'High':     'Critical',
    'Critical': 'Critical',
    'Highest':  'Blocker',
}

TYPE_MAP = {
    'Story':   'Story',
    'Task':    'Technical task',
    'Subtask': 'Technical task',
    'Bug':     'Improvement',
}


def _encode_label(value, classes):
    try:
        return list(classes).index(value)
    except ValueError:
        return 0


def build_effort_features(item_data: dict, sprint_context: dict) -> dict:
    """
    105-feature dict for the XGBoost effort models:
      sprint_load_7d, team_velocity_14d, pressure_index, total_links,
      Type_Code, txt_0 … txt_99

    Text features use the real fitted sklearn TF-IDF vectorizer
    (tfidf_vectorizer.pkl) loaded at startup — no hash approximation.
    """
    title        = item_data.get('title', '')
    description  = item_data.get('description', '')
    item_type    = TYPE_MAP.get(item_data.get('type', 'Task'), 'Technical task')
    story_points = item_data.get('story_points', 5)

    sprint_load    = sprint_context.get('sprint_load_7d', 0)
    team_velocity  = sprint_context.get('team_velocity_14d', 30)
    days_remaining = sprint_context.get('days_remaining', 14)

    pressure_index = story_points / max(1, days_remaining)
    total_links    = description.lower().count('http') + description.count(',') // 3
    type_code      = _encode_label(item_type, TYPE_CLASSES)

    combined_text = f"{title} {description}"
    tfidf = _get_tfidf_vector(combined_text, n_components=100)

    features = {
        'sprint_load_7d':    float(sprint_load),
        'team_velocity_14d': float(team_velocity),
        'pressure_index':    float(pressure_index),
        'total_links':       float(total_links),
        'Type_Code':         float(type_code),
    }
    for i, v in enumerate(tfidf):
        features[f'txt_{i}'] = float(v)

    return features


def build_schedule_risk_features(item_data: dict, sprint_context: dict) -> np.ndarray:
    """
    9 features for XGBClassifier schedule_risk_model (multi:softprob).
    Order: Story_Point, total_links, total_comments, author_total_load,
           link_density, comment_density, pressure_index, Type_Code, Priority_Code
    """
    description  = item_data.get('description', '')
    story_points = item_data.get('story_points', 5)
    priority_ui  = item_data.get('priority', 'Medium')
    item_type_ui = item_data.get('type', 'Task')

    days_remaining = sprint_context.get('days_remaining', 14)
    sprint_load    = sprint_context.get('sprint_load_7d', 0)

    total_links     = float(description.lower().count('http') + description.count(',') // 3)
    total_comments  = float(len(description.split('.')))
    author_load     = float(sprint_load)
    link_density    = total_links / max(1, story_points)
    comment_density = total_comments / max(1, story_points)
    pressure_index  = float(story_points) / max(1, days_remaining)

    prio_model = PRIORITY_MAP.get(priority_ui, 'Major')
    type_model = TYPE_MAP.get(item_type_ui, 'Technical task')
    type_code  = float(_encode_label(type_model, TYPE_CLASSES))
    prio_code  = float(_encode_label(prio_model, PRIO_CLASSES_RISK))

    return np.array([[
        float(story_points),
        total_links,
        total_comments,
        author_load,
        link_density,
        comment_density,
        pressure_index,
        type_code,
        prio_code,
    ]])


def build_productivity_features(item_data: dict, sprint_context: dict,
                                scaler_mean: np.ndarray = None,
                                scaler_scale: np.ndarray = None) -> np.ndarray:
    """9 features for XGBoost productivity model with StandardScaler."""
    story_points   = item_data.get('story_points', 5)
    priority_ui    = item_data.get('priority', 'Medium')
    item_type_ui   = item_data.get('type', 'Task')

    days_remaining = sprint_context.get('days_remaining', 14)
    sprint_load    = sprint_context.get('sprint_load_7d', 0)
    team_velocity  = sprint_context.get('team_velocity_14d', 30)
    days_in_sprint = sprint_context.get('days_since_sprint_start', 0)

    pressure_index  = float(story_points) / max(1, days_remaining)
    velocity_ratio  = float(sprint_load) / max(1, team_velocity)
    sprint_progress = float(days_in_sprint) / max(1, days_in_sprint + days_remaining)

    PROD_TYPE_CLASSES = ['Improvement', 'Story', 'Technical task']
    prio_model = PRIORITY_MAP.get(priority_ui, 'Major')
    type_model = TYPE_MAP.get(item_type_ui, 'Technical task')
    type_code  = float(_encode_label(type_model, PROD_TYPE_CLASSES))
    prio_code  = float(_encode_label(prio_model, PRIO_CLASSES_PROD))

    raw = np.array([[
        float(story_points),
        float(days_remaining),
        float(sprint_load),
        float(team_velocity),
        pressure_index,
        velocity_ratio,
        sprint_progress,
        type_code,
        prio_code,
    ]])

    if scaler_mean is not None and scaler_scale is not None:
        raw = (raw - scaler_mean) / np.where(scaler_scale == 0, 1, scaler_scale)

    return raw


def build_quality_features(item_data: dict, sprint_context: dict) -> np.ndarray:
    """6 features for TabNet quality classifier."""
    story_points  = item_data.get('story_points', 5)
    priority_ui   = item_data.get('priority', 'Medium')
    description   = item_data.get('description', '')

    days_remaining  = sprint_context.get('days_remaining', 14)
    sprint_progress = sprint_context.get('sprint_progress', 0.0)

    prio_model      = PRIORITY_MAP.get(priority_ui, 'Major')
    prio_code       = float(_encode_label(prio_model, PRIO_CLASSES_RISK))
    pressure_index  = float(story_points) / max(1, days_remaining)
    desc_complexity = min(float(len(description)) / 500.0, 1.0)

    return np.array([[
        prio_code,
        float(story_points),
        pressure_index,
        float(days_remaining),
        float(sprint_progress),
        desc_complexity,
    ]])


class FeatureEngineer:
    def __init__(self):
        self.scaler_mean  = None
        self.scaler_scale = None

    def set_scaler(self, mean, scale):
        self.scaler_mean  = mean
        self.scaler_scale = scale

    def extract_features(self, item_data, sprint_context, existing_items=None):
        days_in  = sprint_context.get('days_since_sprint_start', 0)
        days_rem = sprint_context.get('days_remaining', 14)
        total    = days_in + days_rem
        progress = days_in / total if total > 0 else 0.0
        return {
            'story_points':            item_data.get('story_points', 5),
            'priority':                item_data.get('priority', 'Medium'),
            'days_since_sprint_start': days_in,
            'days_remaining':          days_rem,
            'sprint_progress':         progress,
            'sprint_load_7d':          sprint_context.get('sprint_load_7d', 0),
            'team_velocity_14d':       sprint_context.get('team_velocity_14d', 30),
        }

    def prepare_for_effort_model(self, features_dict, item_data, sprint_context):
        return build_effort_features(item_data, sprint_context)

    def prepare_for_schedule_risk_model(self, item_data, sprint_context):
        return build_schedule_risk_features(item_data, sprint_context)

    def prepare_for_quality_risk_model(self, item_data, sprint_context):
        return build_quality_features(item_data, sprint_context)

    def prepare_for_productivity_model(self, item_data, sprint_context):
        return build_productivity_features(
            item_data, sprint_context,
            scaler_mean=self.scaler_mean,
            scaler_scale=self.scaler_scale,
        )


feature_engineer = FeatureEngineer()