/**
 * Smart formatter for time ranges.
 * Input example: "8 - 5" -> "08:00 - 17:00"
 * Input example: "21:30 - 6" -> "21:30 - 06:00"
 */
export const formatTimeRange = (input: string): string => {
  if (!input || !input.includes('-')) return input;

  const parts = input.split('-').map(p => p.trim());
  if (parts.length !== 2) return input;

  const formatTime = (time: string, isEnd: boolean, startTimeHour?: number): string => {
    // Handle cases like "08:00", "8:30", "8"
    const [hours, minutes] = time.split(':').map(p => p?.trim());
    
    if (!hours) return time;
    
    let h = parseInt(hours, 10);
    const m = minutes ? parseInt(minutes, 10) : 0;

    if (isNaN(h)) return time;

    // Infer PM for end time only when it makes sense for a daytime shift.
    // Night shifts (startHour >= 18): end time is next-day morning — never add 12.
    // Day shifts (startHour < 12): if end < start and end <= 12, infer PM (e.g. "8-5" → 17:00).
    if (isEnd && startTimeHour !== undefined) {
      const isNightShift = startTimeHour >= 18;
      if (!isNightShift && h < startTimeHour && h <= 12) {
        h += 12;
      }
    }

    const hh = String(h).padStart(2, '0');
    const mm = String(m).padStart(2, '0');
    return `${hh}:${mm}`;
  };

  const startRaw = parts[0];
  const endRaw = parts[1];

  const startTimeStr = formatTime(startRaw, false);
  const startHour = parseInt(startTimeStr.split(':')[0], 10);
  const endTimeStr = formatTime(endRaw, true, startHour);

  return `${startTimeStr} - ${endTimeStr}`;
};
