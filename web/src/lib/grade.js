// Grading + scoreboard derivation. The data file stores facts; verdicts are derived here.

export const LINES = ['M1', 'M2', 'M3', 'Mercado'];
// Internal key stays 'Mercado' (matches.json, odds CSV, record.py); only the DISPLAY is Pinnacle.
export const LINE_LABELS = { M1: 'M1', M2: 'M2', M3: 'M3', Mercado: 'Pinnacle', M3_frozen: 'M3₀' };
export const LINE_NAMES = { M1: 'Azar', M2: 'Red Neuronal', M3: 'IA con Criterio', Mercado: 'Pinnacle', M3_frozen: 'IA pre-torneo' };
export const LINE_COLORS = { M1: '#64748b', M2: '#3b82f6', M3: '#22c55e', Mercado: '#94a3b8', M3_frozen: '#4d7c5f' };

// The scoreboard grades extra comparison lines that are NOT shown as per-match cells:
//   M3_frozen = the frozen pre-tournament M3 (benchmark) — measures whether updating helped.
// (Mercado_info, the market blend, is added here only if the backtest justifies it.)
export const SCOREBOARD_LINES = ['M1', 'M2', 'M3', 'M3_frozen', 'Mercado'];
export const PINNACLE_NOTE =
  'Pinnacle está considerada por muchos como la casa de apuestas deportivas en línea más sofisticada y más competitiva del mundo. (Wikipedia)';

// Verdict for a scoreline model (M1/M2/M3): acierto on outcome, exacto on exact score.
export function scoreVerdict(pred, result) {
  if (!pred || !result) return null;
  return {
    acierto: pred.pick === result.outcome,
    exacto: pred.home === result.home && pred.away === result.away,
  };
}

// Verdict for Mercado (pick only — no scoreline, never exacto).
export function marketVerdict(pred, result) {
  if (!pred || !result) return null;
  return { acierto: pred.pick === result.outcome, exacto: false };
}

export function verdictFor(line, pred, result) {
  return line === 'Mercado' ? marketVerdict(pred, result) : scoreVerdict(pred, result);
}

// Ranked Probability Score for ordered 3-outcome {home, draw, away}. Lower = better.
export function rps(probs, outcome) {
  const p = [probs.home, probs.draw, probs.away];
  const o = { home: [1, 0, 0], draw: [0, 1, 0], away: [0, 0, 1] }[outcome];
  let cumP = 0, cumO = 0, sum = 0;
  for (let i = 0; i < 2; i++) {
    cumP += p[i]; cumO += o[i];
    sum += (cumP - cumO) ** 2;
  }
  return sum / 2;
}

// Ignorance / logarithmic score: −log2 p[outcome]. Lower = better. Argued to be a
// stricter proper scoring rule than RPS (Wheatcroft 2022) — reported alongside it.
export function logloss(probs, outcome) {
  const p = { home: probs.home, draw: probs.draw, away: probs.away }[outcome];
  return -Math.log2(Math.max(p ?? 0, 1e-12));
}

// Aggregate the running scoreboard across played matches, per line.
export function scoreboard(matches) {
  const acc = Object.fromEntries(
    SCOREBOARD_LINES.map((l) => [l, { jugados: 0, aciertos: 0, exactos: 0, rpsSum: 0, rpsN: 0, rps: null, llSum: 0, llN: 0, logloss: null }])
  );
  for (const m of matches) {
    if (m.status !== 'finalizado' || !m.result) continue;
    for (const line of SCOREBOARD_LINES) {
      const p = m.predictions[line];
      if (!p) continue;
      const s = acc[line];
      s.jugados++;
      const v = verdictFor(line, p, m.result);
      if (v.acierto) s.aciertos++;
      if (v.exacto) s.exactos++;
      if (p.probs) {
        s.rpsSum += rps(p.probs, m.result.outcome); s.rpsN++;
        s.llSum += logloss(p.probs, m.result.outcome); s.llN++;
      }
    }
  }
  for (const l of SCOREBOARD_LINES) {
    const s = acc[l];
    s.rps = s.rpsN ? s.rpsSum / s.rpsN : null;
    s.logloss = s.llN ? s.llSum / s.llN : null;
  }
  // Pinnacle is a 1X2 market, not a scoreline forecast — "exacto" is not applicable
  // (always 0 by construction). Mark it N/A so the board shows "—", not a misleading 0.
  acc.Mercado.exactos = null;
  return acc;
}
