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
}

export default new ApiClient();