// Unit test for the grading engine (grade.js). Run: node web/scripts/test_grade.mjs
import { scoreboard, scoreVerdict, marketVerdict, rps } from '../src/lib/grade.js';

let fails = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ FAIL:', msg); fails++; } else console.log('  ✓', msg); };
const approx = (a, b, e = 1e-9) => Math.abs(a - b) < e;

// --- verdicts ---
const result = { home: 2, away: 1, outcome: 'home' };
ok(JSON.stringify(scoreVerdict({ home: 2, away: 1, pick: 'home' }, result)) === '{"acierto":true,"exacto":true}', 'exact score → acierto + exacto');
ok(JSON.stringify(scoreVerdict({ home: 3, away: 1, pick: 'home' }, result)) === '{"acierto":true,"exacto":false}', 'right winner, wrong score → acierto, not exacto');
ok(JSON.stringify(scoreVerdict({ home: 1, away: 1, pick: 'draw' }, result)) === '{"acierto":false,"exacto":false}', 'wrong outcome → fallo');
ok(marketVerdict({ pick: 'home' }, result).acierto === true && marketVerdict({ pick: 'home' }, result).exacto === false, 'market: outcome-graded, never exacto');

// --- RPS (lower = better; ordered home/draw/away) ---
const rPerfect = rps({ home: 1, draw: 0, away: 0 }, 'home');
const rUniform = rps({ home: 1 / 3, draw: 1 / 3, away: 1 / 3 }, 'home');
ok(approx(rPerfect, 0), 'RPS perfect prediction = 0');
ok(rUniform > rPerfect && rUniform < 0.5, `RPS uniform (${rUniform.toFixed(3)}) between perfect and worst`);

// --- scoreboard aggregation ---
const matches = [
  { status: 'finalizado', result, predictions: {
      M1: { home: 1, away: 1, pick: 'draw', probs: { home: .3, draw: .4, away: .3 } },     // fallo
      M2: { home: 2, away: 1, pick: 'home', probs: { home: .6, draw: .25, away: .15 } },    // acierto + exacto
      M3: null,
      Mercado: { pick: 'home', probs: { home: .55, draw: .25, away: .2 } } } },             // acierto
  { status: 'por_jugarse', result: null, predictions: {
      M1: { home: 1, away: 0, pick: 'home', probs: { home: .5, draw: .3, away: .2 } },
      M2: { home: 2, away: 0, pick: 'home', probs: { home: .7, draw: .2, away: .1 } }, M3: null, Mercado: null } },
];
const sb = scoreboard(matches);
ok(sb.M2.jugados === 1 && sb.M2.aciertos === 1 && sb.M2.exactos === 1, 'M2: 1 jugado, 1 acierto, 1 exacto');
ok(sb.M1.jugados === 1 && sb.M1.aciertos === 0 && sb.M1.exactos === 0, 'M1: 1 jugado, 0 aciertos');
ok(sb.M3.jugados === 0, 'M3 (null preds): 0 jugados');
ok(sb.Mercado.jugados === 1 && sb.Mercado.aciertos === 1 && sb.Mercado.exactos === 0, 'Mercado: 1 acierto, 0 exactos');
ok(sb.M2.rps != null && sb.M1.rps != null && sb.M2.rps < sb.M1.rps, 'M2 RPS < M1 RPS (M2 more confident & right)');

console.log(fails === 0 ? '\nALL PASS' : `\n${fails} FAILED`);
process.exit(fails === 0 ? 0 : 1);
