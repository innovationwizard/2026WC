// Grading + scoreboard derivation. The data file stores facts; verdicts are derived here.

export const LINES = ['M1', 'M2', 'M3', 'Mercado'];
export const LINE_LABELS = { M1: 'M1', M2: 'M2', M3: 'M3', Mercado: 'Mercado' };
export const LINE_NAMES = { M1: 'Azar', M2: 'Red Neuronal', M3: 'Conjunto', Mercado: 'Mercado' };
export const LINE_COLORS = { M1: '#64748b', M2: '#3b82f6', M3: '#22c55e', Mercado: '#94a3b8' };

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

// Aggregate the running scoreboard across played matches, per line.
export function scoreboard(matches) {
  const acc = Object.fromEntries(
    LINES.map((l) => [l, { jugados: 0, aciertos: 0, exactos: 0, rpsSum: 0, rpsN: 0, rps: null }])
  );
  for (const m of matches) {
    if (m.status !== 'finalizado' || !m.result) continue;
    for (const line of LINES) {
      const p = m.predictions[line];
      if (!p) continue;
      const s = acc[line];
      s.jugados++;
      const v = verdictFor(line, p, m.result);
      if (v.acierto) s.aciertos++;
      if (v.exacto) s.exactos++;
      if (p.probs) { s.rpsSum += rps(p.probs, m.result.outcome); s.rpsN++; }
    }
  }
  for (const l of LINES) {
    const s = acc[l];
    s.rps = s.rpsN ? s.rpsSum / s.rpsN : null;
  }
  return acc;
}
