import numpy as np
import re
from datetime import datetime

# Type and Priority label encoders (from artifacts inspection)
TYPE_CLASSES = ['Epic', 'Improvement', 'Missing_Content', 'Story', 'Technical task']
PRIO_CLASSES_RISK  = ['Blocker', 'Critical', 'Major', 'Minor', 'Missing_Content', 'Trivial']
PRIO_CLASSES_PROD  = ['Blocker', 'Critical', 'Major', 'Minor', 'Missing_Content', 'Trivial']

# UI label -> model class mapping
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
    """Replicate sklearn LabelEncoder.transform for known classes"""
    try:
        return list(classes).index(value)
    except ValueError:
        return 0  # fallback to first class

def _tfidf_vector(text, n_components=100):
    """
    Lightweight TF-IDF approximation producing 100-dim float vector.
    Replicates the TfidfVectorizer (max_features=100, stop_words='english')
    used to train the effort model (txt_0 .. txt_99).
    We cannot load the fitted vectorizer (joblib version mismatch) so we
    produce a deterministic hash-based bag-of-words that preserves the
    dimensionality the model expects.
    """
    # Tokenise (same default pattern as sklearn: \b\w\w+\b)
    tokens = re.findall(r'\b\w\w+\b', text.lower())

    # Remove basic English stop-words
    STOP = {
        'the','and','for','are','was','with','this','that','from','have',
        'not','but','will','you','your','they','been','has','had','its',
        'which','can','an','be','is','it','in','of','to','a','as','by',
        'on','at','or','if','do','we','so','up','our','all','use',
    }
    tokens = [t for t in tokens if t not in STOP]

    vec = np.zeros(n_components, dtype=np.float32)
    if not tokens:
        return vec

    # Term frequency
    from collections import Counter
    tf = Counter(tokens)
    total = len(tokens)

    for term, count in tf.items():
        # Deterministic bucket: use hash → position in [0, n_components)
        bucket = abs(hash(term)) % n_components
        tf_val = count / total
        # Smooth IDF approximation (high value for rare/specific words)
        idf = np.log1p(20.0 / (1 + count))
        vec[bucket] += tf_val * idf

    # L2-normalise (sklearn default)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm

    return vec


def build_effort_features(item_data: dict, sprint_context: dict) -> dict:
    """
    Build the 105-feature dict that XGBoost effort models expect:
      sprint_load_7d, team_velocity_14d, pressure_index, total_links, Type_Code,
      txt_0 .. txt_99
    Returns a pandas-style dict keyed by feature name.
    """
    title       = item_data.get('title', '')
    description = item_data.get('description', '')
    item_type   = TYPE_MAP.get(item_data.get('type', 'Task'), 'Technical task')
    story_points = item_data.get('story_points', 5)

    sprint_load     = sprint_context.get('sprint_load_7d', 0)
    team_velocity   = sprint_context.get('team_velocity_14d', 30)
    days_remaining  = sprint_context.get('days_remaining', 14)

    # pressure_index: story_points per remaining day
    pressure_index = story_points / max(1, days_remaining)
    # total_links: approximate from description length (no real link data)
    total_links = description.lower().count('http') + description.count(',') // 3

    type_code = _encode_label(item_type, TYPE_CLASSES)

    # TF-IDF vector of combined text
    combined_text = f"{title} {description}"
    tfidf = _tfidf_vector(combined_text, n_components=100)

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
    Order from risk_artifacts: Story_Point, total_links, total_comments,
    author_total_load, link_density, comment_density, pressure_index,
    Type_Code, Priority_Code
    Label classes from risk_artifacts:
      le_type:  ['Epic','Improvement','Missing_Content','Story','Technical task']
      le_prio:  ['Blocker','Critical','Major','Minor','Missing_Content','Trivial']
    """
    title        = item_data.get('title', '')
    description  = item_data.get('description', '')
    story_points = item_data.get('story_points', 5)
    priority_ui  = item_data.get('priority', 'Medium')
    item_type_ui = item_data.get('type', 'Task')

    days_remaining = sprint_context.get('days_remaining', 14)
    sprint_load    = sprint_context.get('sprint_load_7d', 0)

    # Derived features
    total_links    = float(description.lower().count('http') + description.count(',') // 3)
    total_comments = float(len(description.split('.')))   # sentences ≈ comments
    author_load    = float(sprint_load)
    link_density   = total_links / max(1, story_points)
    comment_density= total_comments / max(1, story_points)
    pressure_index = float(story_points) / max(1, days_remaining)

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
    """
    9 features for XGBoost productivity model.
    Productivity artifacts contain a StandardScaler (9 features).
    le_type: ['Improvement','Story','Technical task']
    le_prio: ['Blocker','Critical','Major','Minor','Missing_Content','Trivial']
    """
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

    type_code = float(_encode_label(type_model, PROD_TYPE_CLASSES))
    prio_code = float(_encode_label(prio_model, PRIO_CLASSES_PROD))

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

    # Apply StandardScaler if available
    if scaler_mean is not None and scaler_scale is not None:
        raw = (raw - scaler_mean) / np.where(scaler_scale == 0, 1, scaler_scale)

    return raw


def build_quality_features(item_data: dict, sprint_context: dict) -> np.ndarray:
    """
    6 features for TabNet quality classifier.
    TabNet model: input_dim=6 (from model_params.json)
    le_prio in le_prio_quality.pkl: LabelEncoder with classes_ stored via joblib
    Using same priority mapping, normalized values.
    """
    story_points   = item_data.get('story_points', 5)
    priority_ui    = item_data.get('priority', 'Medium')
    description    = item_data.get('description', '')

    days_remaining  = sprint_context.get('days_remaining', 14)
    sprint_progress = sprint_context.get('sprint_progress', 0.0)
    sprint_load     = sprint_context.get('sprint_load_7d', 0)

    prio_model = PRIORITY_MAP.get(priority_ui, 'Major')
    # le_prio_quality uses same PRIO_CLASSES_RISK order
    prio_code = float(_encode_label(prio_model, PRIO_CLASSES_RISK))

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
    """Wrapper so existing code can call feature_engineer.extract_features()"""

    def __init__(self):
        self.scaler_mean  = None
        self.scaler_scale = None

    def set_scaler(self, mean, scale):
        self.scaler_mean  = mean
        self.scaler_scale = scale

    def extract_features(self, item_data, sprint_context, existing_items=None):
        """Return a plain dict with all derived scalar features (for summary)"""
        days_in  = sprint_context.get('days_since_sprint_start', 0)
        days_rem = sprint_context.get('days_remaining', 14)
        total    = days_in + days_rem
        progress = days_in / total if total > 0 else 0.0

        return {
            'story_points':          item_data.get('story_points', 5),
            'priority':              item_data.get('priority', 'Medium'),
            'days_since_sprint_start': days_in,
            'days_remaining':        days_rem,
            'sprint_progress':       progress,
            'sprint_load_7d':        sprint_context.get('sprint_load_7d', 0),
            'team_velocity_14d':     sprint_context.get('team_velocity_14d', 30),
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