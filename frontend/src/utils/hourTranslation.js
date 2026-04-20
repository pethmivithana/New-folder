/**
 * hourTranslation.js
 * 
 * MODULE 3: SP to Hours Translation Utilities
 * 
 * SINGLE SOURCE OF TRUTH for SP ↔ Hours conversion throughout the app.
 * 
 * All SP-to-hours conversions MUST use functions from this module for consistency.
 * Default: 1 SP = 8 focus hours (can be customized per space via focus_hours_per_day)
 */

const DEFAULT_HOURS_PER_SP = 8.0;  // Standard: 1 SP = 8 hours of focused work

/**
 * CONSISTENCY CONTRACT:
 * - Backend stores all calculations in STORY POINTS (primary unit)
 * - Hours are ONLY for display/reporting (secondary unit)
 * - Conversion formula: hours = story_points * hours_per_sp
 * - hours_per_sp = focus_hours_per_day from space configuration
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
      return { team_pace: 1.0, hours_per_sp: DEFAULT_HOURS_PER_SP };
    }
    
    const data = await response.json();
    return {
      team_pace: data.team_pace || 1.0,
      hours_per_sp: data.hours_per_sp || DEFAULT_HOURS_PER_SP,
    };
  } catch (error) {
    console.error('[HourTranslation] Error fetching team pace:', error);
    return { team_pace: 1.0, hours_per_sp: DEFAULT_HOURS_PER_SP };
  }
}

/**
 * Convert story points to hours
 * 
 * @param {number} storyPoints - Story points value
 * @param {number} hoursPerSP - Conversion factor (default 8.0)
 * @returns {number} Hours estimate (rounded to 1 decimal)
 */
export function spToHours(storyPoints, hoursPerSP = DEFAULT_HOURS_PER_SP) {
  if (!storyPoints || storyPoints < 0) return 0;
  return Math.round(storyPoints * hoursPerSP * 10) / 10;
}

/**
 * Convert hours to story points
 * 
 * @param {number} hours - Hours value
 * @param {number} hoursPerSP - Conversion factor (default 8.0)
 * @returns {number} Story points estimate (rounded to 1 decimal)
 */
export function hoursToSp(hours, hoursPerSP = DEFAULT_HOURS_PER_SP) {
  if (!hours || hours < 0) return 0;
  return Math.round((hours / hoursPerSP) * 10) / 10;
}

/**
 * Format story points with hours translation for display
 * 
 * Example: formatSPWithHours(5, 8.0) → "5 SP (~40 Hours)"
 * 
 * @param {number} storyPoints - Number of story points
 * @param {number} hoursPerSP - Hours per story point (default 8.0)
 * @returns {string} Formatted display string
 */
export function formatSPWithHours(storyPoints, hoursPerSP = DEFAULT_HOURS_PER_SP) {
  if (!storyPoints || storyPoints < 0) return '0 SP (~0 Hours)';
  
  const estimatedHours = spToHours(storyPoints, hoursPerSP);
  return `${storyPoints} SP (~${estimatedHours} Hours)`;
}

/**
 * Format hours with SP translation for display
 * 
 * Example: formatHoursWithSP(40, 8.0) → "40 Hours (~5 SP)"
 * 
 * @param {number} hours - Number of hours
 * @param {number} hoursPerSP - Hours per story point (default 8.0)
 * @returns {string} Formatted display string
 */
export function formatHoursWithSP(hours, hoursPerSP = DEFAULT_HOURS_PER_SP) {
  if (!hours || hours < 0) return '0 Hours (~0 SP)';
  
  const estimatedSP = hoursToSp(hours, hoursPerSP);
  return `${hours} Hours (~${estimatedSP} SP)`;
}

/**
 * Translate capacity from SP to hours for display
 * 
 * @param {number} sprintCapacitySP - Sprint capacity in story points
 * @param {number} hoursPerSP - Hours per story point
 * @returns {object} { sp: number, hours: number, formatted: string }
 */
export function translateCapacity(sprintCapacitySP, hoursPerSP = DEFAULT_HOURS_PER_SP) {
  const hours = spToHours(sprintCapacitySP, hoursPerSP);
  return {
    sp: sprintCapacitySP,
    hours: hours,
    formatted: `${sprintCapacitySP} SP = ${hours} Hours`,
  };
}
