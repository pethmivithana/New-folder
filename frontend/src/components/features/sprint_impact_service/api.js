const API_BASE_URL = 'http://localhost:8000/api';

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'An error occurred');
      }

      if (response.status === 204) return null;

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // ── Spaces ──────────────────────────────────────────────────────────────────
  async createSpace(data) {
    return this.request('/spaces/', { method: 'POST', body: JSON.stringify(data) });
  }
  async getSpaces() {
    return this.request('/spaces/');
  }
  async getSpace(id) {
    return this.request(`/spaces/${id}`);
  }
  async updateSpace(id, data) {
    return this.request(`/spaces/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  }
  async deleteSpace(id) {
    return this.request(`/spaces/${id}`, { method: 'DELETE' });
  }

  // ── Sprints ─────────────────────────────────────────────────────────────────
  async createSprint(data) {
    return this.request('/sprints/', { method: 'POST', body: JSON.stringify(data) });
  }
  async getSprintsBySpace(spaceId) {
    return this.request(`/sprints/space/${spaceId}`);
  }
  async getSprint(id) {
    return this.request(`/sprints/${id}`);
  }
  async updateSprint(id, data) {
    return this.request(`/sprints/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  }
  async deleteSprint(id) {
    return this.request(`/sprints/${id}`, { method: 'DELETE' });
  }
  async startSprint(id) {
    return this.request(`/sprints/${id}/start`, { method: 'POST' });
  }
  async finishSprint(id, data) {
    return this.request(`/sprints/${id}/finish`, { method: 'POST', body: JSON.stringify(data) });
  }
  async addAssignee(sprintId, assigneeNumber) {
    return this.request(`/sprints/${sprintId}/assignees`, {
      method: 'POST',
      body: JSON.stringify({ assignee_number: assigneeNumber }),
    });
  }
  async removeAssignee(sprintId, assigneeNumber) {
    return this.request(`/sprints/${sprintId}/assignees/${assigneeNumber}`, { method: 'DELETE' });
  }

  // ── Backlog Items ───────────────────────────────────────────────────────────
  async createBacklogItem(data) {
    return this.request('/backlog/', { method: 'POST', body: JSON.stringify(data) });
  }
  async getBacklogItemsBySpace(spaceId) {
    return this.request(`/backlog/space/${spaceId}`);
  }
  async getUnassignedBacklogItems(spaceId) {
    return this.request(`/backlog/space/${spaceId}/backlog`);
  }
  async getBacklogItemsBySprint(sprintId) {
    return this.request(`/backlog/sprint/${sprintId}`);
  }
  async getBacklogItem(id) {
    return this.request(`/backlog/${id}`);
  }
  async updateBacklogItem(id, data) {
    return this.request(`/backlog/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  }
  async deleteBacklogItem(id) {
    return this.request(`/backlog/${id}`, { method: 'DELETE' });
  }
  async updateItemStatus(id, status) {
    return this.request(`/backlog/${id}/status?status=${status}`, { method: 'PATCH' });
  }

  // ── Impact Analysis ─────────────────────────────────────────────────────────
  async getSprintContext(sprintId) {
    return this.request(`/impact/sprints/${sprintId}/context`);
  }
  async analyzeImpact(data) {
    return this.request('/impact/analyze', { method: 'POST', body: JSON.stringify(data) });
  }
  async recordImpactFeedback(logId, data) {
    return this.request(`/impact/logs/${logId}/feedback`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }
  // GET /api/impact/history/{spaceId} — persistent history from MongoDB
  async getAnalysisHistory(spaceId, limit = 50) {
    return this.request(`/impact/history/${spaceId}?limit=${limit}`);
  }

  // ── Analytics & Charts ──────────────────────────────────────────────────────
  // analytics_routes.py is mounted at prefix /api/analytics
  async getSprintBurndown(sprintId) {
    return this.request(`/analytics/sprints/${sprintId}/burndown`);
  }
  async getSprintBurnup(sprintId) {
    return this.request(`/analytics/sprints/${sprintId}/burnup`);
  }
  async getVelocityChart(spaceId) {
    return this.request(`/analytics/spaces/${spaceId}/velocity`);
  }

  // ── AI Story Points ─────────────────────────────────────────────────────────
  async predictStoryPoints(data) {
    return this.request('/ai/predict', { method: 'POST', body: JSON.stringify(data) });
  }

  // ── AI Sprint Goal Alignment ────────────────────────────────────────────────
  async analyzeSprintGoalAlignment(data) {
    return this.request('/ai/analyze-sprint-goal-alignment', { method: 'POST', body: JSON.stringify(data) });
  }

  /**
   * Phase 1 — Check sprint goal alignment using the local Sentence-Transformer
   * (all-MiniLM-L6-v2) 3-layer pipeline.
   *
   * Returns an alignment_state (descriptive only — no action verbs):
   *   CRITICAL_BLOCKER | STRONGLY_ALIGNED | PARTIALLY_ALIGNED | WEAKLY_ALIGNED | UNALIGNED
   *
   * @param {Object}   data
   * @param {string}   data.sprint_goal          – active sprint goal text
   * @param {string}   data.ticket_title         – new ticket title
   * @param {string}   [data.ticket_description] – ticket description (optional)
   * @param {string}   data.priority             – "Critical"|"Blocker"|"High"|"Medium"|"Low"
   * @param {string}   [data.ticket_epic]        – epic the ticket belongs to (optional)
   * @param {string}   [data.sprint_epic]        – primary epic of the sprint (optional)
   * @param {string[]} [data.ticket_components]  – component tags for the ticket (optional)
   * @param {string[]} [data.sprint_components]  – component tags for the sprint (optional)
   *
   * @returns {Promise<{
   *   is_critical_blocker: boolean,
   *   blocker_reason:      string,
   *   semantic_score:      number,    // 0-1, 4 d.p.
   *   semantic_score_pct:  number,    // 0-100 integer for display
   *   alignment_category:  string,    // "HIGHLY_RELEVANT" | "TANGENTIAL" | "UNRELATED"
   *   semantic_reasoning:  string,
   *   epic_aligned:        boolean,
   *   component_overlap:   string,    // "high" | "medium" | "low" | "none"
   *   matched_components:  string[],
   *   metadata_details:    string,
   *   alignment_state:     string,    // "CRITICAL_BLOCKER" | "STRONGLY_ALIGNED" | "PARTIALLY_ALIGNED" | "WEAKLY_ALIGNED" | "UNALIGNED"
   *   alignment_label:     string,    // e.g. "Strongly Aligned"
   *   model_name:          string,    // "all-MiniLM-L6-v2"
   * }>}
   */
  async checkSprintAlignment(data) {
    return this.request('/ai/st-align-sprint-goal', {
      method: 'POST',
      body: JSON.stringify({
        sprint_goal:        data.sprint_goal        ?? '',
        ticket_title:       data.ticket_title       ?? '',
        ticket_description: data.ticket_description ?? '',
        priority:           data.priority           ?? 'Medium',
        ticket_epic:        data.ticket_epic        ?? null,
        sprint_epic:        data.sprint_epic        ?? null,
        ticket_components:  data.ticket_components  ?? [],
        sprint_components:  data.sprint_components  ?? [],
      }),
    });
  }

  /**
   * Phase 3 — Decision Engine.
   * Combines Phase 1 alignment_state + Phase 2 effort/risk + sprint capacity
   * to produce a single Agile action: ADD | DEFER | SPLIT | SWAP.
   *
   * @param {Object} data
   * @param {string} data.alignment_state – from Phase 1 checkSprintAlignment().alignment_state
   * @param {number} data.effort_sp       – estimated story points (from Phase 2 ML model)
   * @param {number} data.free_capacity   – remaining sprint capacity (team_velocity - current_load)
   * @param {string} data.priority        – "Low" | "Medium" | "High" | "Critical"
   * @param {string} data.risk_level      – "LOW" | "MEDIUM" | "HIGH" (derived from schedule risk)
   *
   * @returns {Promise<{
   *   action:          string,  // "ADD" | "DEFER" | "SPLIT" | "SWAP"
   *   rule_triggered:  string,  // e.g. "Rule 5 - Aligned + fits capacity"
   *   reasoning:       string,  // full explanation for the UI card
   *   short_title:     string,  // e.g. "Good Fit - Add to Sprint"
   * }>}
   */
  async getDecision(data) {
    return this.request('/ai/decide', {
      method: 'POST',
      body: JSON.stringify({
        alignment_state: data.alignment_state ?? 'STRONGLY_ALIGNED',
        effort_sp:       data.effort_sp       ?? 5,
        free_capacity:   data.free_capacity   ?? 10,
        priority:        data.priority        ?? 'Medium',
        risk_level:      data.risk_level      ?? 'LOW',
      }),
    });
  }
}

export default new ApiClient();