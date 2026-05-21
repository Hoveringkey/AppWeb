import { formatTimeRange } from './timeUtils';

const cases: [string, string][] = [
  // Daytime shift — end gets inferred as PM
  ['8 - 5',        '08:00 - 17:00'],
  ['7 - 12',       '07:00 - 12:00'],
  // Night shift — end is next-day morning, no PM inference
  ['21:30 - 6',    '21:30 - 06:00'],
  ['21:30 - 06:00','21:30 - 06:00'],
  ['22 - 6',       '22:00 - 06:00'],
  ['23 - 7',       '23:00 - 07:00'],
  ['18 - 2',       '18:00 - 02:00'],
];

let passed = 0;
let failed = 0;

for (const [input, expected] of cases) {
  const result = formatTimeRange(input);
  if (result === expected) {
    console.log(`PASS  formatTimeRange("${input}") === "${expected}"`);
    passed++;
  } else {
    console.error(`FAIL  formatTimeRange("${input}") => "${result}" (expected "${expected}")`);
    failed++;
  }
}

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) throw new Error(`${failed} test(s) failed`);
