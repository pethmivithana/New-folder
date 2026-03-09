/**
 * hourTranslation.js
 * 
 * MODULE 3: SP to Hours Translation Utilities
 * 
 * Converts story points to hours using team pace metrics without requiring
 * developers to work in hours directly. Keeps Agile methodology intact while
 * providing management visibility.
 */

/**
 * Fetch team pace (SP per dev day) from analytics service
 * 
 * @param {string} spaceId - The space/project ID
 * @param {string} apiBaseUrl - API base URL (e.g., http://localhost:8000)
 * @returns {Promise<{team_pace: number, hours_per_sp: number}>}
 */
export async function fetchTeamPace(spaceId, apiBaseUrl = 'http://localhost:8000') {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/analytics/spaces/${spaceId}/team-pace`,
      { method: 'GET', headers: { 'Content-Type': 'application/json' } }
    );
    
    if (!response.ok) {
      console.warn('[HourTranslation] Team pace fetch failed, using defaults');
      return { team_pace: 1.0, hours_per_sp: 8.0 };
    }
    
    const data = await response.json();
    return {
      team_pace: data.team_pace || 1.0,
      hours_per_sp: data.hours_per_sp || 8.0,
    };
  } catch (error) {
    console.error('[HourTranslation] Error fetching team pace:', error);
    return { team_pace: 1.0, hours_per_sp: 8.0 };
  }
}

/**
 * Format story points with hours translation
 * 
 * Example: formatSPWithHours(5, 8.0) → "5 SP (~40 Hours)"
 * 
 * @param {number} storyPoints - Number of story points
 * @param {number} hoursPerSP - Hours per story point (default 8.0)
 * @returns {string} Formatted display string
 */
export function formatSPWithHours(storyPoints, hoursPerSP = 8.0) {
  if (!storyPoints || storyPoints < 0) return '0 SP (~0 Hours)';
  
  const estimatedHours = (storyPoints * hoursPerSP).toFixed(1);
  return `${storyPoints} SP (~${estimatedHours} Hours)`;
}

/**
 * Get hours estimate from story points
 * 
 * @param {number} storyPoints - Number of story points
 * @param {number} hoursPerSP - Hours per story point (default 8.0)
 * @returns {number} Estimated hours
 */
export function getHoursEstimate(storyPoints, hoursPerSP = 8.0) {
  return Math.round(storyPoints * hoursPerSP * 10) / 10; // Round to 1 decimal
}

/**
 * Convert hours back to story points (useful for capacity planning)
 * 
 * @param {number} hours - Number of hours
 * @param {number} hoursPerSP - Hours per story point (default 8.0)
 * @returns {number} Estimated story points
 */
export function getStoryPointsFromHours(hours, hoursPerSP = 8.0) {
  return Math.round((hours / hoursPerSP) * 10) / 10; // Round to 1 decimal
}

/**
 * Translate sprint capacity from SP to hours
 * 
 * @param {number} sprintCapacitySP - Sprint capacity in story points
 * @param {number} hoursPerSP - Hours per story point
 * @returns {object} { sp: number, hours: number, formatted: string }
 */
export function translateCapacity(sprintCapacitySP, hoursPerSP = 8.0) {
  const hours = Math.round(sprintCapacitySP * hoursPerSP * 10) / 10;
  return {
    sp: sprintCapacitySP,
    hours: hours,
    formatted: `${sprintCapacitySP} SP = ${hours} Hours`,
  };
}

/**
 * Create a translation tooltip for displaying SP ↔ Hours
 * 
 * @param {number} storyPoints - Story points
 * @param {number} hoursPerSP - Hours per SP
 * @returns {string} Tooltip text
 */
export function createTooltip(storyPoints, hoursPerSP = 8.0) {
  const hours = getHoursEstimate(storyPoints, hoursPerSP);
  const pace = (8 / hoursPerSP).toFixed(2);
  return (
    `${storyPoints} Story Points = ~${hours} Hours\n` +
    `(Based on team pace of ${pace} SP/day)`
  );
}
