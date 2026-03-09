/**
 * sprintAlignment.js
 * 
 * MODULE 4: Semantic Sprint Goal Alignment Utilities
 * 
 * Checks whether a task aligns with the sprint goal using TF-IDF similarity.
 * Flags potential scope creep automatically.
 */

/**
 * Check sprint goal alignment for a task
 * 
 * @param {string} sprintGoal - The sprint's goal statement
 * @param {string} taskDescription - Full task title and description combined
 * @param {string} apiBaseUrl - API base URL (e.g., http://localhost:8000)
 * @returns {Promise<{alignment_score: number, alignment_level: string, recommendation: string}>}
 */
export async function checkSprintAlignment(
  sprintGoal,
  taskDescription,
  apiBaseUrl = 'http://localhost:8000'
) {
  try {
    if (!sprintGoal || !taskDescription) {
      return {
        alignment_score: 0,
        alignment_level: 'UNALIGNED',
        recommendation: 'Missing sprint goal or task description.',
      };
    }

    const response = await fetch(
      `${apiBaseUrl}/api/ai/align-simple-goal`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sprint_goal: sprintGoal,
          task_description: taskDescription,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error('[SprintAlignment] API error:', error);
      return {
        alignment_score: 0,
        alignment_level: 'UNKNOWN',
        recommendation: 'Could not check alignment. Service unavailable.',
      };
    }

    return await response.json();
  } catch (error) {
    console.error('[SprintAlignment] Error checking alignment:', error);
    return {
      alignment_score: 0,
      alignment_level: 'UNKNOWN',
      recommendation: `Error: ${error.message}`,
    };
  }
}

/**
 * Determine if alignment score indicates scope creep
 * 
 * @param {number} alignmentScore - Score from 0-1
 * @param {number} threshold - Threshold for concern (default 0.4)
 * @returns {boolean} True if likely scope creep
 */
export function isScopeCreep(alignmentScore, threshold = 0.4) {
  return alignmentScore < threshold;
}

/**
 * Get color for alignment badge
 * 
 * @param {string} alignmentLevel - STRONGLY_ALIGNED, PARTIALLY_ALIGNED, UNALIGNED
 * @returns {object} {bg, text, border, accent} color values
 */
export function getAlignmentColors(alignmentLevel) {
  const colors = {
    STRONGLY_ALIGNED: {
      bg: '#ecfdf5',
      text: '#065f46',
      border: '#a7f3d0',
      accent: '#059669',
    },
    PARTIALLY_ALIGNED: {
      bg: '#eff6ff',
      text: '#1e3a8a',
      border: '#bfdbfe',
      accent: '#2563eb',
    },
    UNALIGNED: {
      bg: '#fef2f2',
      text: '#991b1b',
      border: '#fecaca',
      accent: '#dc2626',
    },
    UNKNOWN: {
      bg: '#f9fafb',
      text: '#374151',
      border: '#e5e7eb',
      accent: '#6b7280',
    },
  };

  return colors[alignmentLevel] || colors.UNKNOWN;
}

/**
 * Get icon emoji for alignment level
 * 
 * @param {string} alignmentLevel - STRONGLY_ALIGNED, PARTIALLY_ALIGNED, UNALIGNED
 * @returns {string} Emoji icon
 */
export function getAlignmentIcon(alignmentLevel) {
  const icons = {
    STRONGLY_ALIGNED: '🎯',
    PARTIALLY_ALIGNED: '⚠️',
    UNALIGNED: '🚫',
    UNKNOWN: '❓',
  };

  return icons[alignmentLevel] || '❓';
}

/**
 * Format alignment score as percentage
 * 
 * @param {number} score - Score from 0-1
 * @returns {number} Percentage (0-100)
 */
export function formatAlignmentPercentage(score) {
  return Math.round(score * 100);
}

/**
 * Create a scope creep warning message
 * 
 * @param {number} alignmentScore - Alignment score
 * @param {string} taskTitle - Task title
 * @returns {string} Warning message or empty string
 */
export function getScopeCreepWarning(alignmentScore, taskTitle = '') {
  if (alignmentScore >= 0.4) return '';

  const taskRef = taskTitle ? ` "${taskTitle}"` : '';
  const percentage = formatAlignmentPercentage(alignmentScore);

  if (alignmentScore < 0.2) {
    return (
      `⚠️ SCOPE CREEP ALERT${taskRef} has only ${percentage}% alignment ` +
      `with sprint goal. Consider deferring or re-scoping to align with current sprint focus.`
    );
  }

  return (
    `⚠️ Weak alignment${taskRef} (${percentage}%). Review with team ` +
    `before adding to sprint to ensure it doesn't distract from sprint goals.`
  );
}

/**
 * Batch check alignment for multiple tasks
 * 
 * @param {string} sprintGoal - Sprint goal
 * @param {Array<{title: string, description: string, id?: string}>} tasks - List of tasks
 * @param {string} apiBaseUrl - API base URL
 * @returns {Promise<Array>} Array of alignment results with task IDs
 */
export async function batchCheckAlignment(sprintGoal, tasks, apiBaseUrl = 'http://localhost:8000') {
  const results = await Promise.all(
    tasks.map(async (task) => {
      const description = `${task.title} ${task.description || ''}`.trim();
      const alignment = await checkSprintAlignment(sprintGoal, description, apiBaseUrl);
      return {
        taskId: task.id || task.title,
        taskTitle: task.title,
        ...alignment,
      };
    })
  );

  return results;
}
