// Quick node check of the score() function extracted from index.html,
// so the tested code is the shipped code. Run: node tests/score.test.mjs
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const src = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const consts = src.match(/const GO_H = .*;/)[0];
const fn = src.match(/function score\([\s\S]*?\n\}/)[0];
const score = new Function(`${consts}\n${fn}\nreturn score;`)();

const cases = [
  // [swell m, period s, swell dir °, wind kt, wind dir °, expected]
  [[1.5, 13, 202.5, 4, 250], "GO", "spec: 1.5m @ 13s SSW, calm morning"],
  [[1.0, 9, 225, 4, 250], "OK", "spec: 1.0m @ 9s in window"],
  [[0.5, 11, 225, 2, 90], "SMALL", "spec: 0.5m"],
  [[1.5, 13, 202.5, 15, 270], "OK", "GO swell but onshore 15kt"],
  [[1.5, 13, 202.5, 15, 90], "GO", "windy but offshore (E)"],
  [[2.0, 14, 150, 3, 90], "SMALL", "big but direction out of window"],
  [[1.2, 12, 180, 7.9, 200], "GO", "exact thresholds, sub-8kt wind"],
  [[0.79, 11, 225, 2, 90], "SMALL", "just under rideable floor"],
];

let failed = 0;
for (const [args, want, label] of cases) {
  const [got] = score(...args);
  const ok = got === want;
  if (!ok) failed++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label} → ${got}${ok ? "" : ` (want ${want})`}`);
}
if (failed) {
  console.error(`\n${failed} case(s) failed`);
  process.exit(1);
}
console.log("\nall green 🟢");
