# Chapter 3: Methodology

## 3.1 System Overview and Component Architecture

### 3.1.1 System Overview Diagram

The proposed approach for this component consists of five interconnected phases designed to transform sprint context and new requirements into actionable replanning decisions. The system follows a data-driven pipeline architecture that integrates historical sprint data, real-time sprint state, and requirement properties to generate intelligent recommendations.

**Figure 3.1.1: System Overview Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    SPRINT IMPACT ANALYZER                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [1] Data Acquisition          [2] Feature Engineering      │
│      └─ Sprint History              └─ Requirement Text     │
│      └─ Backlog Items               └─ Numerical Vectors    │
│      └─ Team Velocity               └─ Sprint Context       │
│                                                              │
│              ↓                                               │
│                                                              │
│  [3] Multi-Metric Impact Prediction                         │
│      ├─ Effort Predictor (Linear Regression Ensemble)       │
│      ├─ Schedule Risk (XGBoost Classifier)                  │
│      ├─ Quality Risk (TabNet Deep Learning)                 │
│      └─ Productivity Impact (LSTM Neural Network)           │
│                                                              │
│              ↓                                               │
│                                                              │
│  [4] Sprint Goal Alignment (NLP Analysis)                   │
│      └─ Semantic Similarity Matching                        │
│      └─ Alignment State Classification                      │
│                                                              │
│              ↓                                               │
│                                                              │
│  [5] Decision Engine & Human-in-Loop                        │
│      ├─ Rule-Based Recommendation (ADD/DEFER/SPLIT/SWAP)   │
│      ├─ Capacity Enforcement (80% Safe Limit)              │
│      └─ Decision Execution & Tracking                       │
│                                                              │
│              ↓                                               │
│                                                              │
│  [Dashboard] Impact History & Analytics                     │
│      └─ Action Tracking & Velocity Analysis                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.1.2 Component Overview Diagram

The system consists of three main architectural layers: data layer, intelligence layer, and presentation layer.

**Figure 3.1.2: Component Overview Diagram**

```
┌──────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER (Frontend)               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Impact Analyzer UI                              │   │
│  │  ├─ Requirement Input Form                       │   │
│  │  ├─ Impact Metrics Visualization                 │   │
│  │  ├─ Recommendation Display                       │   │
│  │  └─ Decision Action Buttons                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Analytics Dashboard                             │   │
│  │  ├─ Velocity Charts                              │   │
│  │  ├─ Impact History Timeline                      │   │
│  │  ├─ Action Tracking                              │   │
│  │  └─ Burndown/Burnup Visualization                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Sprint Management UI                            │   │
│  │  ├─ Capacity Display (Safe/Caution/Critical)    │   │
│  │  ├─ Kanban Board                                 │   │
│  │  └─ Sprint Goal Display                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│           INTELLIGENCE LAYER (Backend/Models)            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Feature Engineering Module                      │   │
│  │ ├─ Text Vectorization (TF-IDF)                  │   │
│  │ ├─ Sprint Context Features                      │   │
│  │ └─ Historical Data Normalization                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Prediction Ensemble (4 Models)                  │   │
│  │ ├─ Effort: Linear Regression                    │   │
│  │ ├─ Schedule Risk: XGBoost                       │   │
│  │ ├─ Quality Risk: TabNet                         │   │
│  │ └─ Productivity: LSTM                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ NLP & Alignment Module                          │   │
│  │ ├─ TF-IDF Cosine Similarity                     │   │
│  │ └─ Alignment State Classification               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Decision Engine (Rule-Based)                    │   │
│  │ ├─ ADD/DEFER/SPLIT/SWAP Logic                  │   │
│  │ ├─ Capacity Validation (80% Safe Limit)        │   │
│  │ └─ Risk Threshold Matching                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│            DATA LAYER (MongoDB, Historical)              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐  ┌──────────────────┐             │
│  │  Spaces         │  │  Sprints         │             │
│  │  ├─ max_assign- │  │  ├─ name         │             │
│  │  │  ees         │  │  ├─ goal         │             │
│  │  └─ focus_hours │  │  ├─ capacity_sp  │             │
│  └─────────────────┘  │  └─ status       │             │
│                       └──────────────────┘             │
│                                                          │
│  ┌─────────────────┐  ┌──────────────────┐             │
│  │  Backlog Items  │  │ Recommendation   │             │
│  │  ├─ story_points│  │ Logs             │             │
│  │  ├─ status      │  │ ├─ alignment     │             │
│  │  └─ sprint_id   │  │ ├─ metrics       │             │
│  └─────────────────┘  │ └─ action_taken  │             │
│                       └──────────────────┘             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3.1.3 Machine Learning Flow

The system implements a multi-stage ML pipeline with error handling and fallback mechanisms.

**Figure 3.1.3: Machine Learning and Decision Flow**

```
         NEW REQUIREMENT INPUT
                ↓
     ┌──────────────────────────┐
     │  Input Validation        │
     │  ├─ Gibberish Detection  │
     │  ├─ Min Length Check     │
     │  └─ Technical Term Allow  │
     └──────────────────────────┘
              ↓ (Valid)
     ┌──────────────────────────┐
     │ Feature Engineering      │
     │ ├─ TF-IDF Vectorization  │
     │ ├─ Sprint Context        │
     │ └─ Historical Features   │
     └──────────────────────────┘
              ↓
     ┌──────────────────────────────────────┐
     │  FOUR-MODEL ENSEMBLE PREDICTION      │
     ├──────────────────────────────────────┤
     │                                      │
     │ ┌──────────────────────────────┐    │
     │ │ Model 1: Effort Predictor    │    │
     │ │ Type: Linear Regression      │    │
     │ │ Output: Hours Estimate       │    │
     │ │ Confidence: 75-85%           │    │
     │ └──────────────────────────────┘    │
     │              ↓                       │
     │ ┌──────────────────────────────┐    │
     │ │ Model 2: Schedule Risk       │    │
     │ │ Type: XGBoost Classifier     │    │
     │ │ Output: Spillover Probability│    │
     │ │ Confidence: 80-90%           │    │
     │ └──────────────────────────────┘    │
     │              ↓                       │
     │ ┌──────────────────────────────┐    │
     │ │ Model 3: Quality Risk        │    │
     │ │ Type: TabNet Deep Learning   │    │
     │ │ Output: Defect Injection Risk│    │
     │ │ Confidence: 70-80%           │    │
     │ └──────────────────────────────┘    │
     │              ↓                       │
     │ ┌──────────────────────────────┐    │
     │ │ Model 4: Productivity Impact │    │
     │ │ Type: LSTM Neural Network    │    │
     │ │ Output: Velocity Drop %      │    │
     │ │ Confidence: 65-75%           │    │
     │ └──────────────────────────────┘    │
     │                                      │
     └──────────────────────────────────────┘
         [With Heuristic Fallback if ML Fails]
              ↓
     ┌──────────────────────────┐
     │ NLP Sprint Goal Alignment │
     │ ├─ TF-IDF Similarity      │
     │ ├─ Jaccard Index          │
     │ └─ Alignment State        │
     │    - STRONGLY_ALIGNED     │
     │    - PARTIALLY_ALIGNED    │
     │    - WEAKLY_ALIGNED       │
     │    - UNALIGNED            │
     │    - CRITICAL_BLOCKER     │
     └──────────────────────────┘
              ↓
     ┌──────────────────────────────┐
     │ Rule-Based Decision Engine   │
     │ ├─ Risk Threshold Matching   │
     │ ├─ Capacity Validation       │
     │ └─ Decision Generation       │
     │    - ADD                     │
     │    - DEFER                   │
     │    - SPLIT                   │
     │    - SWAP                    │
     └──────────────────────────────┘
              ↓
     ┌──────────────────────────────┐
     │ Human-in-Loop Decision       │
     │ ├─ Display Recommendation    │
     │ ├─ Show Impact Metrics       │
     │ └─ Manager Makes Choice      │
     └──────────────────────────────┘
              ↓
     ┌──────────────────────────────┐
     │ Action Execution & Tracking  │
     │ ├─ Update Sprint/Backlog     │
     │ ├─ Adjust Capacity           │
     │ └─ Log Decision History      │
     └──────────────────────────────┘
```

---

## 3.2 Implementation Approach

### 3.2.1 System Architecture and Data Flow

The system is built on a modern three-tier architecture:

**Backend (Python FastAPI)**
- Handles all ML model inference and decision logic
- Manages MongoDB data persistence
- Provides REST APIs for frontend communication
- Implements error handling with graceful fallbacks

**Frontend (React/JavaScript)**
- Displays impact analyzer interface with requirement input form
- Visualizes impact metrics in real-time
- Shows recommendation and allows human decision-making
- Tracks action history and analytics

**Database (MongoDB)**
- Stores spaces, sprints, backlog items, and historical data
- Maintains recommendation logs for impact tracking
- Persists sprint goal alignment analyses

### 3.2.2 The Four Machine Learning Models

Since the nature of sprint impact is multifaceted, four distinct machine learning models were implemented to predict complementary dimensions of project health:

#### **Model 1: Effort Predictor (Linear Regression Ensemble)**

**Purpose:** Estimate the actual effort (in hours) required for a new requirement

**Architecture:**
- Input: Requirement title, description, historical similar items
- Feature Engineering: TF-IDF vectors of requirement text, complexity metrics, dependency count
- Training Data: Historical backlog items with actual hours spent
- Output: Point estimate with confidence interval

**Implementation Details:**
- Uses scikit-learn's LinearRegression with cross-validation
- Handles missing data through mean imputation
- Provides upper/lower bounds for uncertainty quantification
- Fallback: Heuristic uses SP × focus_hours_per_day (default 8 hours per SP)

**Model Performance:**
- Accuracy on validation set: 78-85%
- Handles edge cases through feature normalization
- Reports confidence score with predictions

#### **Model 2: Schedule Risk Predictor (XGBoost Classifier)**

**Purpose:** Predict probability of task spillover beyond sprint boundary

**Architecture:**
- Input: Requirement effort, sprint progress, days remaining, team capacity
- Algorithm: Gradient Boosting (XGBoost) with class weighting
- Training Data: Historical sprint outcomes (completed vs. incomplete items)
- Output: Spillover probability (0-100%)

**Implementation Details:**
- Weights minority class (failed items) heavily to avoid optimism bias
- Considers temporal features (days elapsed vs. days remaining)
- Analyzes current team load relative to capacity
- Fallback: Heuristic based on effort-per-day analysis

**Risk Categories:**
- Safe: < 30% spillover probability
- Moderate: 30-60%
- High Risk: > 60%
- Critical: >= 100% (impossible to complete)

#### **Model 3: Quality Risk Predictor (TabNet Deep Learning)**

**Purpose:** Estimate probability of defect injection from requirement change

**Architecture:**
- Input: Requirement description complexity, change scope, affected areas
- Algorithm: TabNet (tabular data deep learning architecture)
- Training Data: Historical items with recorded defect counts post-implementation
- Output: Quality risk percentage (0-100%)

**Implementation Details:**
- Captures non-linear relationships in tabular data
- Uses attention mechanisms to identify important features
- Detects integration complexity from text analysis
- Fallback: Heuristic based on requirement text complexity and dependency count

**Quality Risk Indicators:**
- Safe: < 30% quality risk
- Elevated: 30-60%
- High Risk: > 60%

#### **Model 4: Productivity Impact Predictor (LSTM Neural Network)**

**Purpose:** Estimate velocity drop from context switching caused by mid-sprint additions

**Architecture:**
- Input: Sprint stage, new requirement size, team load, historical context-switch impact
- Algorithm: Long Short-Term Memory (LSTM) neural network
- Training Data: Historical velocity patterns during sprint disruptions
- Output: Productivity drop percentage

**Implementation Details:**
- Temporal model captures sprint progress stage effects
- Earlier additions have greater impact (more context switches)
- Considers team size and individual assignment patterns
- Fallback: Heuristic estimates productivity loss based on sprint stage

**Productivity Impact:**
- Minimal: < 10% velocity drop
- Moderate: 10-25%
- Significant: 25-40%
- Severe: > 40%

### 3.2.3 Sprint Capacity Calculation and Management

The system implements intelligent capacity management with historical learning:

**Capacity Calculation Algorithm:**

```
First Sprint Capacity:
  capacity_sp = assignee_count × 8 SP

Subsequent Sprints:
  previous_velocity = completed_sp_last_sprint
  completion_ratio = completed_sp / committed_sp
  new_capacity = (previous_velocity × completion_ratio) 
                 × (new_assignees / previous_assignees)
  
  Minimum floor: capacity_sp = assignee_count × 4 SP
```

**Capacity Display and Enforcement:**

- **Healthy Zone (0-80%):** Safe to add items
- **Caution Zone (80-99%):** Warning shown, user can proceed at own risk
- **Critical Zone (>= 100%):** Additions blocked, must remove items first
- **Safe Buffer:** 80% limit shown as recommendation, 100% as hard limit

### 3.2.4 Sprint Goal Alignment Analysis (NLP Logic)

The system uses Natural Language Processing to assess requirement alignment with sprint objectives:

**Alignment Assessment Process:**

```
1. Text Preprocessing:
   └─ Tokenization, lowercasing, stop-word removal

2. Feature Extraction:
   ├─ TF-IDF vectorization of sprint goal and requirement
   └─ Historical keyword mapping

3. Similarity Calculation:
   ├─ Cosine similarity (primary): sim ≥ 0.7 = aligned
   ├─ Jaccard index (fallback): for short texts
   └─ Keyword overlap analysis

4. Alignment Classification:
   ├─ score ≥ 0.75: STRONGLY_ALIGNED (low risk)
   ├─ 0.50-0.75: PARTIALLY_ALIGNED (moderate risk)
   ├─ 0.25-0.50: WEAKLY_ALIGNED (high risk)
   ├─ < 0.25: UNALIGNED (distraction)
   └─ Negative keywords: CRITICAL_BLOCKER (cannot add)
```

**Alignment Scoring:**

- Layer 1: Critical Blocker Detection (incompatible keywords)
- Layer 2: TF-IDF Cosine Similarity (0-1 scale)
- Layer 3: Metadata Traceability (historical alignment patterns)
- Layer 4: Context Validation (sprint stage, team capacity)

### 3.2.5 Rule-Based Decision Engine and Human-in-Loop Workflow

The decision engine synthesizes all four ML predictions and alignment analysis into a single recommendation:

**Decision Logic:**

```
IF alignment_state == CRITICAL_BLOCKER:
    RECOMMEND: DEFER (with high confidence)

ELSE IF effort_hours > remaining_sprint_hours:
    IF alignment == STRONGLY_ALIGNED:
        RECOMMEND: SPLIT (split into parts)
    ELSE:
        RECOMMEND: DEFER (too much work)

ELSE IF schedule_risk > 60%:
    IF priority == HIGH AND alignment == STRONGLY_ALIGNED:
        RECOMMEND: ADD (with caution)
    ELSE:
        RECOMMEND: DEFER (schedule too tight)

ELSE IF quality_risk > 60%:
    IF effort_low AND alignment_high:
        RECOMMEND: ADD (manage quality separately)
    ELSE:
        RECOMMEND: DEFER (quality concerns)

ELSE IF productivity_impact > 25%:
    IF alignment == STRONGLY_ALIGNED:
        RECOMMEND: SPLIT (reduce context switch)
    ELSE:
        RECOMMEND: DEFER

ELSE:
    RECOMMEND: ADD (low risk across all dimensions)

# Final Check:
IF remaining_capacity < required_effort:
    FINAL_DECISION: CANNOT_ADD (capacity exceeded)
ELSE:
    FINAL_DECISION: USER_CHOICE (system recommendation ready)
```

**Decision Options Available to Manager:**

1. **ADD** - Add requirement to current active sprint
   - Updates sprint load immediately
   - Recalculates capacity consumption
   - Triggers capacity warning if >= 80%

2. **DEFER** - Move to backlog for future sprint
   - Maintains sprint focus
   - Prevents scope creep
   - Allows sprint goal completion

3. **SPLIT** - Divide requirement between sprint and backlog
   - High-priority portion added to sprint
   - Lower-priority portion deferred
   - Auto-calculates split ratio (70% sprint / 30% backlog)

4. **SWAP** - Replace similar-sized item in sprint with new requirement
   - Maintains sprint capacity
   - Allows priority adjustment
   - Moves displaced item to backlog

**Human-in-Loop Logic:**

The system does NOT make the final decision. Instead, it:
1. Displays all four impact metrics with risk levels
2. Shows sprint goal alignment state
3. Presents system recommendation with explanation
4. Allows manager to override and choose alternative
5. Tracks the chosen action in recommendation log

### 3.2.6 Story Point Estimation with Fibonacci Sequence

The system enforces the Fibonacci sequence (1, 2, 3, 5, 8, 13, 21) for story points:

**SP Suggestion Algorithm:**

```
INPUT: Requirement title, description
OUTPUT: Suggested story points from Fibonacci sequence

1. Extract Features:
   ├─ Text length and complexity
   ├─ Find historically similar requirements
   └─ Analyze technical complexity keywords

2. Find Similar Items:
   ├─ TF-IDF similarity to historical backlog
   ├─ Return top 3 matches with SPs
   └─ Average their SPs with confidence weighting

3. Heuristic Adjustment:
   ├─ If no historical match, use complexity heuristic
   ├─ Short/simple requirement: 1-3 SP
   ├─ Medium complexity: 5-8 SP
   └─ High complexity: 13-21 SP

4. Validate Against Fibonacci:
   ├─ Find nearest valid Fibonacci number
   ├─ Return suggested SP with confidence score
   └─ Allow manual override by user

5. User Input Validation:
   ├─ If user provides non-Fibonacci number
   ├─ Suggest nearest valid Fibonacci number
   └─ Block submission if outside 1-21 range
```

**Confidence Levels:**

- High (75-100%): Strong historical match found
- Medium (50-75%): Partial match or heuristic-based
- Low (< 50%): Insufficient data, recommend manual estimation

### 3.2.7 Impact Action History Tracking and Analytics

The system maintains comprehensive logs of all impact analyses and decisions:

**Recorded Data:**

```
For Each Requirement Analysis:
├─ Requirement title and description
├─ Sprint goal and context
├─ System recommendation (ADD/DEFER/SPLIT/SWAP)
├─ User's chosen action
├─ All four impact metrics (effort, schedule, quality, productivity)
├─ Sprint goal alignment state
├─ Alignment score and reasoning
├─ Timestamp of analysis
├─ Timestamp of action taken
└─ Optional user notes

Analytics Aggregation:
├─ Total requirements analyzed per sprint
├─ Distribution of recommendations vs. actions taken
├─ Action effectiveness tracking (did requirement work out?)
├─ Velocity impact correlation
└─ Alignment accuracy metrics
```

**History Query Endpoints:**

- Sprint Impact History: All analyses for single sprint
- Space Impact History: Trend analysis across all sprints
- Action Distribution: Breakdown of ADD/DEFER/SPLIT/SWAP usage
- Alignment Accuracy: How often alignment predictions matched reality

### 3.2.8 Error Handling and Model Fallback Mechanisms

The system implements graceful degradation when ML models fail:

**Error Handling Strategy:**

```
FOR EACH ML PREDICTION:
  TRY:
    result = ml_model.predict(features)
    confidence = model_confidence_score
  CATCH Exception:
    result = heuristic_estimate(features)
    confidence = LOW (flagged as using fallback)
    error_flag = ML_FAILED_USING_HEURISTIC

FINAL OUTPUT:
├─ predictions (from ML or heuristic)
├─ model_confidence: HIGH or LOW
├─ using_heuristic: boolean flag
└─ individual error flags per metric
```

**Heuristic Fallbacks:**

- **Effort:** 5 hours per story point
- **Schedule Risk:** Based on effort-per-day analysis
- **Quality Risk:** Based on requirement complexity and keywords
- **Productivity:** Based on sprint stage and requirement size

**Confidence Reporting:**

Users see indicators when fallback heuristics are used, ensuring transparency about model reliability.

---

## 3.3 Development Tools and Technologies

### 3.3.1 Backend Technologies

**Python**
- Primary language for ML model development and backend logic
- Chosen for versatility in algorithmic programming and data manipulation

**FastAPI Framework**
- Modern Python web framework for building REST APIs
- Async support for handling concurrent requests
- Automatic request validation and documentation

**Machine Learning Libraries:**

- **Scikit-Learn**: Linear regression for effort prediction, feature extraction (TF-IDF)
- **XGBoost**: Gradient boosting for schedule risk classification
- **TabNet**: Deep learning for quality risk on tabular data
- **TensorFlow/Keras**: Neural network implementation for LSTM productivity model
- **NumPy/Pandas**: Data manipulation and numerical computing

**Natural Language Processing:**
- **TF-IDF Vectorizer**: Text feature extraction and similarity matching
- **Jaccard Index**: Alternative similarity metric for short texts

**Database:**
- **MongoDB**: NoSQL database for flexible schema storage of sprints, backlog items, and logs
- **PyMongo**: Python driver for MongoDB operations

### 3.3.2 Frontend Technologies

**React/JavaScript**
- Component-based UI development
- Real-time updates using SWR (stale-while-revalidate) caching

**Tailwind CSS**
- Utility-first CSS framework for responsive design
- Consistent theming and accessibility

**APIs:**
- Fetch API for REST communication with backend
- Async/await for handling asynchronous operations

### 3.3.3 Development Environment

**VS Code**
- Primary IDE for development
- Integrated debugging and Git support
- Extensions for Python, JavaScript, and MongoDB

**Python Virtual Environment**
- Isolated Python environment for dependency management
- pip/poetry for package management

**Git/GitHub**
- Version control and collaboration
- Branch-based development workflow

### 3.3.4 Model Training and Validation

**Data Splitting:**
- 70% training, 20% validation, 10% test set
- Stratified splits for balanced class representation

**Validation Metrics:**
- Regression models: MAE (Mean Absolute Error), RMSE (Root Mean Squared Error)
- Classification models: Precision, Recall, F1-Score, ROC-AUC
- Ensemble: Cross-validation scores

**Hyperparameter Tuning:**
- Grid search for algorithm parameter optimization
- Validation on held-out dataset to prevent overfitting

---

## 3.4 Data Management and Preprocessing

### 3.4.1 Data Sources

**Historical Sprint Data:**
- Completed sprints from project management system
- Actual effort vs. estimated effort
- Velocity patterns over time

**Backlog Item Data:**
- Requirement titles and descriptions
- Assigned story points
- Actual implementation hours
- Defect count post-implementation

**Sprint Context:**
- Sprint duration and dates
- Team composition and assignments
- Sprint goals and objectives

### 3.4.2 Data Preprocessing

**Text Preprocessing:**
1. Tokenization of requirement text
2. Lowercasing and special character removal
3. Stop-word removal
4. Stemming/lemmatization where applicable

**Feature Normalization:**
- Effort metrics scaled to 0-1 range
- Temporal features normalized by sprint duration
- Team size features scaled relative to maximum

**Class Weighting:**
- Applied to address imbalanced datasets
- Minority class (failed sprints) weighted higher
- Ensures models focus on high-risk scenarios

### 3.4.3 Handling Missing Data

**Strategy:**
- Mean imputation for numerical features
- Mode imputation for categorical features
- Removal of rows with > 30% missing values
- Forward-fill for temporal data

---

## 3.5 System Validation Approach

### 3.5.1 Model Validation

**Cross-Validation:**
- 5-fold cross-validation for model stability assessment
- Ensures models generalize beyond training data

**Backtesting:**
- Test models on historical sprint data
- Measure prediction accuracy for completed requirements
- Compare recommendations to actual outcomes

### 3.5.2 System Integration Testing

**Scenario-Based Testing:**
- Test each decision path (ADD/DEFER/SPLIT/SWAP)
- Verify capacity enforcement at thresholds (80%, 100%)
- Validate sprint goal alignment for various requirement types

**User Acceptance Testing:**
- Involve project managers in testing workflows
- Validate that recommendations align with domain expertise
- Ensure UI is intuitive and decision-making process clear

### 3.5.3 Performance Metrics

**Accuracy Metrics:**
- Alignment prediction accuracy vs. manual assessment
- Decision recommendation accuracy vs. expert judgment
- Effort estimation error (MAPE: Mean Absolute Percentage Error)

**System Performance:**
- API response time < 2 seconds for impact analysis
- Database query efficiency for large sprint histories
- Frontend rendering performance with large datasets

---

This methodology section covers the complete approach, architecture, and implementation details of the Sprint Impact Analyzer component, grounded in machine learning principles, data engineering best practices, and human-centered decision-making design.
