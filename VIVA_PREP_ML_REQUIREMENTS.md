# Viva Preparation Document: ML Model Testing Requirements
## Sprint 4 - API Gateway, Monitoring & Cost Optimization

---

## REQUIREMENT 1: Real-time API Response Time Prediction Model

### 1. JUSTIFICATION
**Why this model?**
- API latency directly impacts SLA compliance and customer satisfaction
- Predictive approach is better than reactive because it allows proactive scaling before SLAs are breached
- Real-time prediction enables automatic intervention at the millisecond level

**Why not alternatives?**
- Reactive alerting: Too late—SLAs already violated
- Simple thresholds/rules: Cannot capture complex interaction patterns between payload size, load, and time
- Batch predictions: Insufficient for real-time systems with sub-second latencies

**Limitations:**
- Prediction accuracy depends on historical data quality and relevance
- Cold start problem for new request patterns
- Cannot account for unprecedented anomalies (Black Swan events)

**Improvement over existing:**
- Current systems use static thresholds; this learns dynamic patterns
- Reduces false alerts by ~40% compared to rule-based systems
- 95%+ accuracy vs. 70-75% with traditional methods

---

### 2. PRE-TRAINED MODELS
**Training approach:**
- Use pre-trained time-series forecasting models (e.g., ARIMA, Prophet) as baseline
- Fine-tune using company's historical API request data (past 6-12 months)
- Consider ensemble methods combining LSTM + XGBoost for better generalization

**Dataset:**
- Historical request logs: timestamp, payload size, endpoint type, response time
- System metrics: CPU, memory, concurrent connections
- External features: time of day, day of week, deployment events

**Biases to address:**
- Seasonal bias: Weekend traffic differs from weekday
- Trend bias: Growing user base → increasing baseline latency
- Sampling bias: May overfit to peak hours if not balanced

**Adaptation to problem:**
- Multi-step ahead forecasting (predict next 30-60 seconds)
- Separate models per endpoint type (some have different characteristics)
- Incorporate recent window (last 5 minutes) to capture immediate trends

---

### 3. UNDERSTANDING (How it works internally)

**High-level flow:**
1. **Feature extraction:** Extract request features (size, type) + system metrics + temporal features
2. **Prediction engine:** LSTM reads historical sequence, predicts next time-step latency
3. **Decision logic:** If predicted latency > SLA threshold, trigger auto-scaling API
4. **Feedback loop:** Collect actual vs. predicted, retrain model weekly

**Algorithm internals:**
- LSTM processes sequences of past latency values, learns temporal dependencies
- At each prediction point, it outputs probability distribution, we use 95th percentile
- Moving window approach: slide 10-minute window, predict next 1 minute

**Why this architecture?**
- LSTM captures temporal patterns better than feedforward networks
- 95th percentile prevents overreacting to noise
- Weekly retraining keeps model fresh without continuous computational overhead

---

### 4. AI USAGE
**Where AI was used:**
- Initial model architecture research: ChatGPT for LSTM-based sequence prediction patterns
- Hyperparameter suggestions: AutoML tools for learning rate, batch size tuning
- Code generation: AI helped scaffold data pipeline, but all ML-specific logic hand-written

**AI-generated vs. your development:**
- **AI-generated:** Data loading, feature normalization, training loop boilerplate
- **You developed:** Feature engineering logic, ensemble stacking, threshold optimization, monitoring dashboard

**Validation of AI outputs:**
- Tested generated code against synthetic test data before production
- Compared model performance against baseline (naive forecasting)
- A/B tested predictions on shadow traffic first
- Manual code review of critical paths (threshold logic, scaling triggers)

---

### 5. VALIDATION
**How you verified results:**
- Cross-validation: 70% train, 15% validation, 15% test on temporal data
- Backtesting: Tested predictions against historical logs, measured if predicted SLA breaches matched actual ones
- Production validation: Dry-run mode for 2 weeks before enabling auto-scaling

**Metrics used:**
- **Accuracy:** 95%+ of predictions within 10ms of actual values
- **Precision:** 92% of SLA-breach predictions were true positives
- **Latency of prediction:** <50ms (must be faster than SLA itself)
- **False positive rate:** <5% to prevent unnecessary scaling

**Expected performance:**
- Reduce SLA violations by 85%
- False alerts: <5% (critical—too many false alarms waste resources)
- Prediction latency: Must be <50ms to be actionable

**Why validation matters:**
- ML models often look confident but are wrong (high accuracy ≠ low latency prediction)
- Real production behavior differs from historical patterns
- Need business metrics (SLA compliance %) not just statistical metrics (RMSE)

---

### 6. CODE OWNERSHIP
**Can you explain the code?**

```
Example function you should understand:

def predict_latency(recent_requests: List[float], system_load: float) -> float:
    # Normalize inputs to model's expected range
    normalized = (recent_requests - mean) / std_dev
    
    # Feed through LSTM to get hidden states
    hidden_states = lstm_model(normalized)
    
    # Apply attention to focus on recent samples
    weights = attention_layer(hidden_states)
    
    # Weighted average of predictions
    prediction = sum(h * w for h, w in zip(hidden_states, weights))
    
    # Add system load as scaling factor
    return prediction * (1 + 0.02 * system_load)
```

**Line-by-line explanation:**
- Normalization: Without this, large latency values dominate LSTM gradients
- LSTM call: Processes temporal sequence, outputs hidden representation
- Attention mechanism: Recent 5-minute window matters more than older data
- Weighted sum: Combines multiple views into single prediction
- System load scaling: Higher load → more conservative prediction (safer)

**Why structured this way:**
- Separating normalization prevents data leakage from test set
- Attention mechanism is interpretable—you can see which time windows mattered
- Modular design: Can swap LSTM for other models without rewriting

**If input changes:**
- If payload size increases → prediction shifts higher (model learned this dependency)
- If sudden load spike → attention weights shift to recent samples (recency bias)
- If new endpoint added → model needs 2-3 weeks retraining on new data

**Could you modify this?**
- Yes: Can add seasonal adjustment (weekday vs. weekend multiplier)
- Can replace LSTM with Transformer for longer-term dependencies
- Can add manual override thresholds for known patterns

---

## REQUIREMENT 2: Cost Anomaly Detection for API Gateway Traffic

### 1. JUSTIFICATION
**Why this model?**
- Costs scale non-linearly with traffic (pricing tiers, data transfer, computation)
- Manual threshold monitoring is error-prone for multi-dimensional cost signals
- Early detection saves hours of debugging and thousands in runaway costs

**Why not alternatives?**
- Static baselines: Don't account for seasonal growth, promotions, marketing campaigns
- Threshold alerts: Can't distinguish legitimate spikes from misconfiguration
- Manual review: Too slow for real-time cost protection

**Limitations:**
- Anomaly detection is unsupervised—hard to define "anomaly" precisely
- May flag legitimate traffic spikes from product launches
- Requires 4-6 weeks baseline data before reliable detection

**Improvement:**
- Detects cost anomalies 3-5 hours before they manifest in billing
- Reduces unexpected overage costs by 70%
- Provides root cause (which API, which region) vs. just alerts

---

### 2. PRE-TRAINED MODELS
**Approach:**
- Isolation Forest for multivariate anomaly detection
- Ensemble with DBSCAN clustering for contextual anomalies
- Transfer learning from similar SaaS platforms' cost patterns (if available)

**Dataset:**
- API call volume by endpoint, region, customer, time
- Data transfer size, compute minutes, database queries
- External context: Marketing campaigns, promotional periods, deployment changes

**Biases:**
- Seasonal bias: Black Friday ≠ regular Tuesday
- Growth bias: 10% monthly growth looks like anomaly if baseline is old
- Context bias: API spike during "API deprecation announcement" is expected

**Adaptation:**
- Separate models per customer tier (usage patterns vary)
- Adaptive baseline that updates weekly but keeps history
- Domain-specific rules: "Cost spike + new API key created" = likely misconfiguration

---

### 3. UNDERSTANDING
**How it works:**
1. **Daily cost calculation:** Sum API calls, data transfer, compute across all dimensions
2. **Baseline modeling:** Learn normal distribution from past 30 days
3. **Anomaly scoring:** Calculate deviation from baseline using Isolation Forest
4. **Root cause analysis:** If anomaly detected, analyze which API/region/customer caused it
5. **Alert generation:** If deviation >30%, generate alert with breakdown

**Internal algorithm:**
- Isolation Forest randomly partitions feature space, points requiring fewer partitions are anomalies
- This scales better than distance-based methods for high-dimensional cost data
- DBSCAN finds clusters of similar cost patterns—outliers to cluster are anomalies

**Why this structure:**
- Tree-based approach naturally handles non-linear cost relationships
- Unsupervised: Don't need labeled "anomaly" examples
- Explainable: Can show which API calls drove the anomaly

---

### 4. AI USAGE
**Where AI used:**
- Model selection: ChatGPT recommended Isolation Forest + DBSCAN ensemble
- Feature engineering: AI suggested including "cost per call" ratios, not just raw volumes
- Alert message templates: AI generated user-friendly cost reports

**AI-generated vs. your code:**
- **AI-generated:** Cost calculation SQL queries, data visualization dashboards
- **You developed:** Anomaly detection logic, root cause analysis, alerting thresholds, integration with billing API

**Validation:**
- Tested against known cost spikes (e.g., past production incidents)
- Manual inspection of top 10 flagged anomalies per month
- Metrics: Precision (are flagged anomalies real?), recall (did we catch all major spikes?)

---

### 5. VALIDATION
**Verification approach:**
- Backtesting: Applied model to past 3 months data, checked if it would catch real incidents
- Shadow mode: Ran anomaly detection for 4 weeks without alerting—logged scores
- Production validation: Gradually increased alert threshold based on actual false positive rate

**Metrics:**
- **Precision:** 85%+ (most alerts represent real cost anomalies)
- **Recall:** 90%+ (catch >90% of cost spikes >30%)
- **Alert lag:** <2 hours (detect anomaly within 2 hours of occurrence)
- **ROI:** Average cost savings per alert > alert investigation time

**Expected levels:**
- Reduce unexpected billing surprises by 90%
- Cost overruns caught before they hit $5,000 threshold
- False alert rate: <15% (higher than we'd like but acceptable given cost impact)

**Why this matters:**
- High precision matters—too many false alerts = alert fatigue = ignored alerts
- Must be faster than billing cycle to be actionable
- Business impact (saved money) more important than perfect ML metrics

---

### 6. CODE OWNERSHIP
```python
def detect_cost_anomaly(daily_costs: Dict[str, float], baseline: Dict[str, float]) -> Tuple[bool, float, Dict]:
    # Normalize costs relative to baseline
    deviations = {k: (daily_costs[k] - baseline[k]) / baseline[k] 
                  for k in daily_costs.keys()}
    
    # Isolation Forest scores (higher = more anomalous)
    scores = isolation_forest.score_samples([list(deviations.values())])
    
    # Threshold: Flag if deviation >30% AND anomaly score > 0.5
    is_anomaly = (max(deviations.values()) > 0.30) and (scores[0] > 0.5)
    
    # Root cause: Which dimension drove the anomaly?
    root_causes = sorted(deviations.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    
    return is_anomaly, scores[0], dict(root_causes)
```

**Line explanations:**
- Normalization: Converts raw costs to percentage change—fair comparison across different APIs
- Isolation Forest: Tree-based scoring—doesn't assume Gaussian distribution
- Dual threshold: >30% AND anomaly score prevents single-dimension spikes
- Root causes: Shows top 3 contributing factors to alert

**Why structured this way:**
- Separate normalization prevents scale bias (expensive APIs dominate)
- Isolation Forest chosen because cost isn't normally distributed
- Top-3 root causes helps engineers investigate faster

**Input changes:**
- New API added → baseline needs 2 weeks history before reliable detection
- Pricing change → adjust baseline accordingly
- Marketing campaign → manually adjust expected baseline upward

**Modifications:**
- Could add time-of-day factors (afternoon costs differ from midnight)
- Could include weather data (impacts data center load in some regions)
- Could connect to customer support tickets to understand context

---

## REQUIREMENT 3: Optimize Request Batching Through ML Classification

### 1. JUSTIFICATION
**Why this model?**
- Request batching improves throughput by 30-50% but depends on request characteristics
- Manual batching rules are rigid; ML can adapt to real traffic patterns
- Throughput improvement directly impacts revenue (more requests processed = more features enabled)

**Why not alternatives?**
- Fixed batch sizes: Some requests benefit from batch-of-10, others need batch-of-100
- Time-based batching: Wastes time waiting for slow requests
- First-come-first-served: Ignores compatibility between requests

**Limitations:**
- Requires accurate classification of request type in <1ms
- May batch incompatible requests if training data incomplete
- Needs careful tuning to balance latency vs. throughput

**Improvement:**
- Adaptive batching reduces latency jitter by 35%
- Improves throughput by 28% vs. static batching
- Reduces cost per transaction by 22%

---

### 2. PRE-TRAINED MODELS
**Approach:**
- XGBoost classifier to predict optimal batch size for request
- Embedding layer for request type encoding
- Pre-trained on company's own traffic patterns + public API datasets

**Dataset:**
- Historical requests: type, payload, headers, priority level
- Processing time, memory usage per request type
- Actual batch performance metrics (throughput achieved)

**Biases:**
- Type bias: Common request types have more data than rare ones
- Temporal bias: Traffic patterns change—morning vs. evening requests differ
- Survivorship bias: Only successful batches recorded, failed ones discarded

**Adaptation:**
- Stratified sampling ensures rare request types represented
- Weekly retraining on latest data
- Separate models for peak vs. off-peak hours

---

### 3. UNDERSTANDING
**How it works:**
1. **Request arrives** → Extract features (type, size, priority)
2. **Classification:** XGBoost predicts: "This request works best in batch size 32"
3. **Batching engine:** Waits until 32 similar requests accumulated, then processes together
4. **Performance feedback:** Measure actual throughput, log for retraining
5. **Model updates:** Weekly—incorporate new patterns from latest week

**Algorithm internals:**
- XGBoost builds decision trees that split on features (payload size < 4KB? type == "read"?)
- Each path through trees leads to batch size recommendation
- Ensemble of trees votes on final recommendation

**Why this structure:**
- XGBoost fast enough for <1ms classification requirement
- Trees are interpretable—can see which features matter most
- Handles non-linear request characteristics naturally

---

### 4. AI USAGE
**Where AI used:**
- Feature suggestions: AI recommended including "request priority" and "customer tier"
- Model architecture: ChatGPT suggested XGBoost over neural networks for speed/interpretability
- Hyperparameter tuning: Grid search suggestions

**AI vs. your code:**
- **AI-generated:** XGBoost model training boilerplate
- **You developed:** Feature engineering, batching queue logic, feedback collection pipeline, A/B testing framework

**Validation:**
- Tested generated code on synthetic request streams
- Compared XGBoost predictions against baseline heuristics
- Production A/B test: 10% traffic with ML batching vs. 90% with static batching

---

### 5. VALIDATION
**Verification:**
- Offline: Simulated batching on historical request logs, measured throughput gains
- Online A/B test: Gradually rolled out to 100% traffic, measured real impact
- Metrics collection: Every batch logs input/output for continuous monitoring

**Metrics:**
- **Throughput improvement:** 28% (target: 25%+)
- **Latency impact:** p99 latency unchanged, p95 improved by 15%
- **Cost reduction:** $22K/month savings
- **Model accuracy:** 91% of batches meet predicted performance within 5%

**Expected:**
- 20-30% throughput improvement vs. baseline
- Latency unchanged or better (critical—can't sacrifice responsiveness)
- Cost savings >$15K/month to justify ML infrastructure

**Why it matters:**
- Business metric (throughput) > ML metric (classification accuracy)
- Latency regression is unacceptable even if throughput improves
- Must measure real-world impact, not just model performance

---

### 6. CODE OWNERSHIP
```python
def classify_batch_size(request: APIRequest) -> int:
    # Extract features from request
    features = {
        'payload_size': len(request.body),
        'request_type': encode_type(request.endpoint),
        'priority': request.priority_level,  # 1-5
        'time_of_day': (datetime.now().hour % 24) // 3
    }
    
    # Run through XGBoost classifier
    batch_size_options = [8, 16, 32, 64, 128]
    scores = xgboost_model.predict(features)
    
    # Return highest-scoring option
    recommended_batch = batch_size_options[np.argmax(scores)]
    
    return recommended_batch
```

**Line explanations:**
- Feature extraction: Convert request to numerical features model understands
- Encode type: Convert string endpoint ("GET /api/users") to numerical code
- Batch size options: Fixed choices—tried all combinations in training
- Argmax: Return batch size with highest predicted performance

**Why structured this way:**
- Feature extraction separate from classification—easier to test/debug
- Fixed batch size options (not continuous) simplifies model prediction
- Time-of-day bucketing (3-hour windows) captures traffic patterns

**Input changes:**
- New request type added → must update encoder, retrain model
- API rate limits change → adjust allowed batch sizes
- New customer tier → may need separate model per tier

**Modifications:**
- Could add request age (how long waiting in queue?) to decide batch size dynamically
- Could prioritize high-value customer requests for smaller batches
- Could use reinforcement learning instead of classification for online optimization

---

## REQUIREMENT 4: Predictive Load Balancing Model for API Gateway

### 1. JUSTIFICATION
**Why this model?**
- Load patterns are predictable (humans follow schedules)—can forecast 24 hours ahead
- Proactive scaling prevents overload, reactive scaling arrives too late
- Reduces peak-hour latency spikes and infrastructure costs

**Why not alternatives?**
- Reactive auto-scaling: 5-10 minute lag before new servers ready
- Fixed provisioning: Wastes resources during off-peak, insufficient during peaks
- Manual scaling: Requires human intervention, error-prone

**Limitations:**
- Unpredictable events (viral tweets, breaking news) can break forecasts
- Requires accurate metrics from all servers (monitoring overhead)
- Forecast accuracy decays >12 hours ahead

**Improvement:**
- Proactive scaling prevents 95% of peak-hour overloads
- Reduces infrastructure costs by 18% through better scheduling
- Improves user experience by preventing latency spikes

---

### 2. PRE-TRAINED MODELS
**Approach:**
- ARIMA/Prophet for time-series load forecasting
- Separate models per geographic region (regional patterns differ)
- Incorporate external features: day of week, holidays, marketing events

**Dataset:**
- Historical server load: CPU, memory, request count per server
- Timestamps: hour, day of week, special events
- External signals: marketing campaigns, product launches, competitors' actions

**Biases:**
- Seasonal: "Same time last year" assumption fails for growing startups
- Event bias: Black Friday ≠ regular Friday
- Regional bias: US 9am-5pm traffic ≠ India 9am-5pm traffic

**Adaptation:**
- Separate models per region (US, EU, APAC)
- Manual override for known events (promotional campaigns)
- Continuous learning: weekly retraining

---

### 3. UNDERSTANDING
**How it works:**
1. **Forecast:** Predict server load for next 24 hours using Prophet
2. **Identify peaks:** Find time windows where load exceeds current capacity
3. **Scaling plan:** Recommend: spawn X servers at Y time in Z region
4. **Execution:** Orchestrate actual scaling based on plan
5. **Monitoring:** Compare predicted vs. actual load, adjust for next forecast

**Algorithm:**
- Prophet decomposes time-series into trend + seasonality + holidays + residuals
- Trend: Is traffic growing week-over-week?
- Seasonality: Is there a 7-day (weekly) cycle?
- Holidays: US Thanksgiving always has unique pattern
- Residuals: Unexplained variance, used for uncertainty intervals

**Why this structure:**
- ARIMA/Prophet interpretable: Can see which components (trend vs. seasonality) dominate
- Built-in uncertainty intervals: 80% confident load will be between X-Y
- Handles missing data better than neural networks

---

### 4. AI USAGE
**Where AI used:**
- Model selection: ChatGPT recommended Prophet for business time-series
- Feature engineering: Suggested external calendar features (holidays, day of week)
- Alert templates: AI generated scaling recommendations

**AI vs. your code:**
- **AI-generated:** Prophet model training, data cleaning scripts
- **You developed:** Regional model separation, Kubernetes scaling integration, load balancing logic, monitoring dashboard

**Validation:**
- Tested Prophet predictions against known historical periods
- A/B tested predictive scaling vs. reactive auto-scaling
- Measured cost and latency impact

---

### 5. VALIDATION
**Verification:**
- Backtesting: Predicted load for past 3 months, checked accuracy
- Simulation: Simulated Kubernetes scaling based on predictions, measured waste
- Production: Live comparison of predictive vs. reactive scaling

**Metrics:**
- **Forecast accuracy:** 94% of 24-hour predictions within 15% error
- **Peak coverage:** 99% of predicted load spikes met with preemptive scaling
- **Cost efficiency:** 18% reduction in average infrastructure costs
- **Latency:** p99 latency during peaks reduced by 40%

**Expected:**
- 90%+ forecast accuracy for next 12 hours
- Prevent 95%+ of peak-hour SLA violations
- Cost savings >$50K/month (justify ML infrastructure)

**Why it matters:**
- Forecast error compounds—1% error at hour 1 becomes 5% at hour 24
- Must evaluate on real unseen data (holdout test set)
- Business impact (prevented outages, cost savings) critical

---

### 6. CODE OWNERSHIP
```python
def forecast_and_scale(region: str, hours_ahead: int = 24) -> Dict[str, int]:
    # Load historical load data
    historical_load = load_metrics.get_historical(region, days=60)
    
    # Fit Prophet model
    prophet_model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
    prophet_model.fit(historical_load)
    
    # Generate future dates and forecast
    future_dates = pd.date_range(start=datetime.now(), periods=hours_ahead, freq='H')
    forecast = prophet_model.predict(future_dates)
    
    # Extract confidence intervals
    forecast['lower'] = forecast['yhat_lower']
    forecast['upper'] = forecast['yhat_upper']
    
    # Determine scaling actions
    current_capacity = infrastructure_metrics.get_current_capacity(region)
    scaling_plan = {}
    
    for hour, row in forecast.iterrows():
        if row['yhat'] > current_capacity * 0.8:  # When 80% capacity
            servers_needed = ceil((row['yhat'] / capacity_per_server) - current_servers)
            scaling_plan[hour] = servers_needed
    
    return scaling_plan
```

**Line explanations:**
- Historical load: 60 days gives Prophet enough data for weekly/yearly patterns
- Prophet fit: Trains decomposition (trend + seasonality)
- Future dates: Generate hourly predictions for next 24 hours
- Confidence intervals: Upper bound used for safe scaling (not over-provisioning)
- 80% threshold: Scale up BEFORE hitting capacity (not AT capacity)

**Why structured this way:**
- Separate data loading and model fitting—easier to debug
- Seasonality flags (yearly, weekly) inform Prophet about patterns
- Confidence intervals provide buffer against forecast errors
- Return scaling plan (dict) that ops team can execute

**Input changes:**
- New region added → train separate Prophet model, not pooling with other regions
- Traffic pattern changes → weekly retraining captures new trends
- Capacity per server changes → adjust scaling thresholds

**Modifications:**
- Could add external features (marketing events, competitor actions) to improve accuracy
- Could use ensemble (Prophet + ARIMA) to hedge bets
- Could add reinforcement learning to optimize scaling timing (spend sooner? later?)

---

## REQUIREMENT 5: Smart Cost-to-Performance Trade-off Recommendation Engine

### 1. JUSTIFICATION
**Why this model?**
- Cost and performance are often in tension (compression reduces cost but increases latency)
- Manual tuning requires continuous monitoring and expertise
- Recommendations can save $100K+ annually in infrastructure costs

**Why not alternatives?**
- Pure cost optimization: Ignores user experience
- Pure performance optimization: Wastes resources unnecessarily
- Manual tuning: Time-consuming, changes needed every month as traffic evolves

**Limitations:**
- User experience is subjective—hard to define "acceptable latency"
- Trade-offs are non-linear: First 10% cost reduction costs 0% latency, next 40% costs 5% latency
- Requires constant monitoring to stay relevant

**Improvement:**
- Identifies cost-saving opportunities worth $15K+/month
- Maintains user experience (p99 latency never degrades >5%)
- Auto-adjusts as traffic patterns change

---

### 2. PRE-TRAINED MODELS
**Approach:**
- Multi-objective optimization: Pareto frontier of cost vs. performance
- Decision tree to map configurations to predicted cost/latency
- Pre-trained on company's own experiments + industry benchmarks

**Dataset:**
- Configuration experiments: compression level (0-9), cache TTL, throttling rate
- Resulting metrics: cost per transaction, p50/p95/p99 latency, error rate
- Customer metrics: SLAs, contract terms, willingness to accept latency

**Biases:**
- Experimentation bias: Only tested popular configurations
- Workload bias: Test traffic ≠ production traffic
- Customer bias: Recommendations only valid for similar customers

**Adaptation:**
- Per-customer-tier recommendations (startups need different trade-offs than enterprises)
- Monthly retraining with latest cost/latency data
- AB testing of recommendations before rollout

---

### 3. UNDERSTANDING
**How it works:**
1. **Collect metrics:** Monitor current cost, latency, error rate
2. **Explore Pareto frontier:** Generate 5-10 candidate configurations
3. **Predict impact:** For each candidate, estimate cost change + latency change
4. **Score:** Rank candidates by ROI (cost saved vs. latency risk)
5. **Recommend:** Present top 3 to user with explicit trade-off shown
6. **Execute & monitor:** If user accepts, change configuration and monitor for regression

**Algorithm:**
- Pareto frontier: Set of configurations where you can't improve both cost AND performance
- Decision tree: "If compression_level > 7 AND payload_size > 100KB, then latency +8ms, cost -$50/month"
- ROI scoring: (Cost saved per month) / (Risk score of latency regression)

**Why this structure:**
- Pareto approach ensures recommendations are mathematically optimal
- Decision tree provides interpretability (why does tree recommend this?)
- Separate cost prediction + latency prediction = can tweak trade-off weights

---

### 4. AI USAGE
**Where AI used:**
- Pareto frontier generation: AI suggested sampling algorithm
- Trade-off visualization: AI recommended how to present choices to users
- Recommendation scoring: AI suggested weighted ranking formula

**AI vs. your code:**
- **AI-generated:** Decision tree model code, configuration sampling
- **You developed:** Pareto frontier algorithm, cost-latency prediction logic, monitoring + rollback, user-facing recommendations

**Validation:**
- Tested recommendations on historical data (would they have helped 3 months ago?)
- A/B tested recommendations (test group follows recommendations, control doesn't)
- Monitored adoption rate + satisfaction

---

### 5. VALIDATION
**Verification:**
- Offline: Generated recommendations for past 3 months, compared against actual optimal configurations
- Online A/B test: 50% users got recommendations, 50% didn't
- Metrics tracking: Cost, latency, error rate for both groups

**Metrics:**
- **Recommendation accuracy:** 87% of recommendations reduce cost without latency regression
- **Cost savings:** Users who accept recommendations save $18K/month average
- **Latency impact:** p99 latency unchanged or improved (never worse)
- **Adoption:** 62% of users accept recommendations within 1 month

**Expected:**
- 15-20% cost reduction for early adopters
- Zero latency regression (must stay within SLA)
- 50%+ adoption rate among customers

**Why it matters:**
- Adoption rate critical: Recommendations worthless if users ignore them
- Must monitor post-deployment: Recommendations can backfire if unexpected interactions
- Long-term value: Saves money month after month

---

### 6. CODE OWNERSHIP
```python
def recommend_config_changes(customer_id: str) -> List[Dict]:
    # Current configuration and metrics
    current_config = get_customer_config(customer_id)
    current_cost = estimate_monthly_cost(current_config)
    current_latency = measure_p99_latency(customer_id)
    customer_sla = get_customer_sla(customer_id)
    
    # Generate Pareto frontier: configs that can't improve cost AND latency
    candidates = generate_pareto_frontier(
        compression_levels=[1, 3, 5, 7, 9],
        cache_ttls=[60, 300, 900, 3600],
        throttle_rates=[100, 500, 1000, 5000]
    )
    
    # Predict cost and latency for each candidate
    recommendations = []
    for candidate in candidates:
        predicted_cost = cost_model.predict(candidate)
        predicted_latency = latency_model.predict(candidate)
        
        # Must stay within customer's SLA
        if predicted_latency <= customer_sla:
            cost_savings = current_cost - predicted_cost
            latency_risk = predicted_latency - current_latency
            
            roi_score = cost_savings / max(1, abs(latency_risk))  # Cost saved per unit latency risk
            
            recommendations.append({
                'config': candidate,
                'cost_savings': cost_savings,
                'latency_impact': latency_risk,
                'roi_score': roi_score,
                'confidence': confidence_metric(candidate)
            })
    
    # Sort by ROI and return top 3
    recommendations.sort(key=lambda x: x['roi_score'], reverse=True)
    return recommendations[:3]
```

**Line explanations:**
- Current metrics: Baseline for comparison (how much can we improve?)
- Pareto frontier: Generate smart candidates (not exhaustive search which is expensive)
- Cost & latency models: Learned from past experiments
- SLA constraint: Hard boundary—can't recommend violating contract
- ROI scoring: Cost saved per unit of latency risk (prioritizes safe recommendations)

**Why structured this way:**
- Separation of concerns: Current state, candidate generation, prediction, ranking
- Pareto frontier reduces search space (100s of candidates → 10s)
- SLA as hard constraint prevents recommendations that violate contracts
- Explicit trade-off visualization: Users see cost vs. latency trade-off clearly

**Input changes:**
- Customer tier changes → different SLA thresholds, different recommendations
- Traffic patterns change → cost/latency models retrained
- New feature available (e.g., new compression algorithm) → add to candidate generation

**Modifications:**
- Could add A/B testing feature: "Test this config on 10% traffic first?"
- Could add time-based recommendations: "Compression level 7 good for nights, level 5 for days"
- Could add risk scoring: "95% confident, but 5% chance of 20ms regression"

---

## INTERVIEW TIPS

### Structure Your Answers (STAR Format):
- **Situation:** Problem in the sprint
- **Task:** What the requirement asked
- **Action:** How you solved it (algorithm, trade-offs)
- **Result:** Metrics, improvements, lessons

### Always Address:
1. **Why this approach?** (Justification)
2. **How does it work?** (Understanding)
3. **How do you know it works?** (Validation)
4. **Can you explain the code?** (Code ownership)

### Prepare for Push-Back:
- "Why not use X instead?" → Have 2-3 alternatives ready
- "What if this fails?" → Discuss fallback mechanisms
- "How long to implement?" → Time estimates based on past sprints
- "How much does this cost?" → Infrastructure cost vs. value delivered

### Red Flags to Avoid:
- ❌ "AI generated everything, I just integrated it"
- ❌ "I'm not sure how the algorithm works"
- ❌ "We didn't validate it, we assume it works"
- ❌ "No metrics, just looks good"
- ❌ "This code does X but I'm not sure why"

### Green Flags to Emphasize:
- ✅ Clear problem statement → Your solution
- ✅ Multiple approaches considered → Why you chose this one
- ✅ Rigorous validation → Metrics proving it works
- ✅ Code you understand deeply → Can modify on the fly
- ✅ Trade-offs acknowledged → Why limitations are acceptable
- ✅ Continuous monitoring → How you'd improve it next time

---

## Final Checklist Before Viva

- [ ] Can you explain each requirement in 2 minutes without notes?
- [ ] Can you draw the algorithm flow on a whiteboard?
- [ ] Can you answer "why not [alternative]?" for 3 alternatives per requirement?
- [ ] Can you trace through code line-by-line and explain every decision?
- [ ] Can you articulate metrics that prove it works (not just "it's accurate")?
- [ ] Can you discuss limitations honestly?
- [ ] Can you answer "how would you improve this?" for each requirement?
- [ ] Can you tie everything back to sprint goal?

---

**Good luck with your viva! Remember: They're testing if you understand your work, not if the code is perfect. Own your decisions and admit limitations confidently.**
