# AGILE REPLANNING DECISION SUPPORT SYSTEM
## Final Year IT Project - Demonstration Speech

**Duration: 7-10 minutes**

---

## PART 1: THE PROBLEM (1 minute)

Good morning. Let me start with a scenario most of you in software development know too well.

It's day 8 of a 2-week sprint. Your team has committed to 25 story points. You're tracking well—the burndown chart shows a healthy slope. Then at 10 AM, the Product Owner arrives with news: "Critical production bug found in authentication. We need a hotfix ASAP. That's 5 story points minimum."

What happens next? The team looks at the Scrum Master. The Scrum Master opens Jira. They see the sprint capacity, they see the existing work... and then what? They guess. 

Should we add it to the sprint? Will it break the team? Will something else spill over? Will we compromise on quality to ship faster? Nobody has concrete answers. So the decision becomes reactive, often wrong, and always stressful.

**[SPEAKER NOTE: Pause and look at the audience]**

This is the chaos of mid-sprint scope changes. And despite having sophisticated tools like Jira, Azure DevOps, and Monday.com tracking every user story, none of them can answer the fundamental question: *"What will actually happen if we add this work?"*

---

## PART 2: THE RESEARCH GAP (1.5 minutes)

I studied existing tools, and here's what I found: they are **excellent at tracking work** but **terrible at predicting impact**.

Jira shows you:
- What's in the sprint
- Burndown charts
- Velocity trends

But it doesn't tell you:
- How many story points will this new requirement *actually take* (effort prediction)?
- Will the team still deliver on time (schedule risk analysis)?
- Will rushed code introduce bugs (quality risk estimation)?
- Will the pressure reduce team throughput (productivity impact)?

The research gap is clear: **Agile tools track work, but they don't predict consequences.**

Academic literature in software engineering—particularly research by Boehm (1981) on cost estimation and later work by McConnell (2006) on schedule risk—shows that predictive models significantly improve decision quality. Yet this knowledge remains largely absent from commercial Agile tools.

**[SPEAKER NOTE: Gesture to the screen]**

My contribution is to bridge this gap: to bring predictive analytics—specifically Machine Learning models trained on software engineering principles—into the sprint decision-making process.

---

## PART 3: THE SOLUTION (30 seconds)

**Introducing the Agile Replanning Decision Support System.**

A web-based application that uses AI to evaluate urgent sprint requirements in real-time, predicting their impact across four dimensions—effort, schedule risk, quality, and team productivity—and uses a decision engine to recommend one of four outcomes:

1. **Add** — The requirement fits safely within sprint capacity
2. **Defer** — Too risky mid-sprint; move it to backlog
3. **Split** — Break it into smaller chunks to fit capacity
4. **Swap** — Replace lower-priority work with this urgent requirement

All within seconds. All with transparent reasoning.

---

## PART 4: SYSTEM CONTEXT — THE FOUNDATIONAL APP (2 minutes)

Before we get to the AI engine, let me walk you through the foundational Agile framework this system is built on.

**[SPEAKER NOTE: Click to Project Spaces screen]**

Everything starts with **Project Spaces**—a workspace where teams define their sprint cadence, team size, and baseline parameters. This is where the system learns about capacity and context.

From there, we move into **Sprints**. The system creates sprints with locked durations (typically 2 weeks), and here's where the first innovation appears:

**[SPEAKER NOTE: Click to Backlog screen]**

When adding user stories to the backlog, the system uses **NLP-powered Story Point Suggestions**. You describe a requirement in natural language—"Add two-factor authentication"—and the system estimates the complexity and effort, suggesting story points. This is faster than Planning Poker and reduces groupthink.

Once a sprint is running, teams use the **Kanban Board**—a full-screen interface with four columns: To-Do, In Progress, In Review, Done. No drag-and-drop fighting. No modal popups. Just clean, intuitive task management.

**[SPEAKER NOTE: Click Kanban board - show columns]**

And critically, the system maintains **historical velocity data**. Every completed sprint is recorded:
- Sprint 1: 25 SP committed, 25 SP delivered (100% velocity)
- Sprint 2: 30 SP committed, 22 SP delivered (73% velocity—we had spillover)
- Sprint 3: 20 SP committed, 20 SP delivered (100% velocity)

This gives us a **baseline velocity of 22.33 SP per sprint**. This is essential for the predictive models that come next.

---

## PART 5: THE CLIMAX — THE AI IMPACT ANALYZER (3 minutes)

Now, imagine it's day 8 of Sprint 4. The team has committed to 30 SP. They've completed 24 SP so far. That leaves 6 SP of capacity.

**[SPEAKER NOTE: Click to dashboard and show Sprint 4 status]**

The urgent requirement arrives: *"Database optimization—critical for Q4 compliance. Estimated at 8 story points. High priority."*

The team clicks "Analyze Impact." Here's what happens in the system:

### Step 1: Semantic Goal Alignment

**[SPEAKER NOTE: Show the current sprint goal on screen]**

The system fetches the sprint goal: *"Implement Stripe payment integration and ensure 99.9% uptime."*

It compares the new requirement—database optimization—against this goal using NLP semantic similarity. Database optimization is tangentially related (uptime matters) but not core to Stripe integration. **Alignment Score: 0.62/1.0** (moderately aligned).

### Step 2: The Four ML Predictive Models Fire Simultaneously

The system creates a feature vector of the incoming requirement and passes it through four independently trained ML models:

#### Model 1: Effort Prediction (XGBoost Regressor)

**[SPEAKER NOTE: Show effort prediction results]**

Input features:
- Story points: 8
- Priority: High
- Description length and complexity
- Historical similar tasks

The XGBoost model is trained on 500+ historical tickets from across your company. It outputs:

**Estimated Effort Range:**
- **Lower Bound: 7 SP** (optimistic—if no blockers)
- **Median Estimate: 9 SP** (most likely)
- **Upper Bound: 12 SP** (pessimistic—including unknowns)

Why three estimates? Because software estimation is inherently uncertain. The median of 9 SP already exceeds available capacity (6 SP).

#### Model 2: Schedule Risk Classification (XGBoost Classifier)

**[SPEAKER NOTE: Explain the features]**

The system evaluates:
- Days remaining (6 days in a 10-day sprint)
- Team load (current 24/30 SP utilization)
- Pressure index (urgency × story points ÷ time remaining)
- Historical spillover patterns

**Output: 67% Schedule Risk**

**Interpretation:** If we add this work, there's a two-thirds probability something won't ship on time. This aligns with McConnell's research on schedule pressure—adding scope to a partially-committed sprint significantly increases delay risk.

#### Model 3: Quality Risk (PyTorch TabNet Classifier)

**[SPEAKER NOTE: Emphasize this model]**

Quality is often sacrificed under schedule pressure. The TabNet model predicts defect likelihood by analyzing:
- Story point size (larger = more surface area for bugs)
- Priority/criticality (does pressure lead to corner-cutting?)
- Team velocity trends (are we already fatigued?)
- Description complexity

**Output: 58% Defect Risk**

**Interpretation:** At 58% probability, rushing this task introduces significant quality risk. For a compliance-critical database change, this is unacceptable.

#### Model 4: Productivity Impact (Hybrid Ensemble: XGBoost + PyTorch Neural Network)

**[SPEAKER NOTE: Note the hybrid approach]**

This model answers: *"If we add this work, will the team's overall throughput collapse?"*

It uses:
- Context-switching cost (moving from Stripe work to database work)
- Cognitive load (how many different domains must the team manage?)
- Historical productivity under high-load sprints

**Output: -15% Productivity Impact**

**Interpretation:** Adding this work will reduce team efficiency by 15%. Instead of delivering 22 SP, they'll only deliver about 18.7 SP. Combined with the new 9 SP requirement, the math breaks down.

### Step 3: The Rule Engine Decision

Now the system has all four predictions:
1. **Effort:** 9 SP (exceeds capacity by 3 SP)
2. **Schedule Risk:** 67% (high)
3. **Quality Risk:** 58% (high)
4. **Productivity Impact:** -15% (significant)

The Rule Engine evaluates in this order:

**Rule 1 (DEFER threshold):** If (Schedule Risk > 60% AND Effort Median > Available Capacity), recommend DEFER.

✓ Triggered. But let's check other rules.

**Rule 2 (SPLIT evaluation):** Can we decompose the requirement?

The system suggests: *"Database optimization could be split: (a) Index optimization (3 SP) + (b) Query analysis (6 SP)."*

The first chunk (3 SP) fits capacity and reduces quality risk. But the second chunk still has schedule risk.

**Rule 3 (SWAP consideration):** Is there lower-priority work we can displace?

The system identifies: *"UI polish task (5 SP) in the sprint is marked 'nice to have.'"*

If we remove this and add the first split of database optimization (3 SP), we maintain velocity and address the critical need.

**Final Recommendation:**

**[SPEAKER NOTE: Highlight this prominently on screen]**

```
RECOMMENDED ACTION: SPLIT & SWAP

✓ Add "Database Index Optimization" (3 SP, High Priority)
  Reason: Fits capacity, directly supports uptime goal
  
↕ Swap out "UI Polish Task" (5 SP, Low Priority)
  Reason: Non-critical, can move to next sprint
  
→ Defer "Query Analysis Phase" (6 SP) to Sprint 5
  Reason: Schedule risk too high for this sprint
```

**Impact Summary:**
- Sprint 4 capacity: 30 SP
- Current work: 24 SP
- After SPLIT & SWAP: 24 - 5 + 3 = 22 SP
- Remaining capacity: 8 SP (safety buffer preserved)
- Predicted Quality Risk (revised): 23% (acceptable)
- Predicted Schedule Risk (revised): 18% (low)

---

## CLOSING (30 seconds)

**[SPEAKER NOTE: Make eye contact with examiners]**

This system transforms Agile decision-making from guesswork into data-driven reasoning. In a world where scope creep is inevitable, giving teams real-time impact analysis—backed by ML and academic research—lets them say "yes" to the right work at the right time.

Thank you.

---

## [SPEAKER NOTES SUMMARY FOR PRESENTERS]

| Timestamp | Action |
|-----------|--------|
| 0:00 | Start with auth bug scenario |
| 1:00 | Transition to problem statement |
| 2:30 | Show research gap slide |
| 3:00 | Introduce solution (show title slide) |
| 3:30 | Click to Project Spaces screenshot |
| 4:00 | Show NLP story point suggestion in action |
| 4:30 | Display Kanban board full-screen |
| 5:00 | Show Sprint 4 status with 24/30 SP utilization |
| 5:30 | Input new requirement and click "Analyze Impact" |
| 5:45 | Show Effort Prediction output (7-12 SP range) |
| 6:15 | Display Schedule Risk: 67% |
| 6:45 | Highlight Quality Risk: 58% |
| 7:15 | Show Productivity Impact: -15% |
| 7:45 | Reveal final Rule Engine recommendation |
| 8:15 | Recap SPLIT & SWAP decision |
| 8:45 | Show final impact summary dashboard |
| 9:00 | Closing remarks |
