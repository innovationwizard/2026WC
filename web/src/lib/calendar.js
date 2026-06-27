// Date selection + formatting for the calendar and the two single-day cards.

export function groupByDate(matches) {
  const map = new Map();
  for (const m of matches) {
    if (!map.has(m.date)) map.set(m.date, []);
    map.get(m.date).push(m);
  }
  return [...map.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1));
}

// Recientes = most recent single date with >= 1 finished match.
export function recientesDate(matches) {
  const dates = matches.filter((m) => m.status === 'finalizado').map((m) => m.date).sort();
  return dates.length ? dates[dates.length - 1] : null;
}

// Próximos = next single date with >= 1 unplayed match.
export function proximosDate(matches) {
  const dates = matches.filter((m) => m.status === 'por_jugarse').map((m) => m.date).sort();
  return dates.length ? dates[0] : null;
}

export function matchesOn(matches, date) {
  return date ? matches.filter((m) => m.date === date) : [];
}

export function fmtDay(iso) {
  const d = new Date(iso + 'T12:00:00');
  const s = new Intl.DateTimeFormat('es', { weekday: 'long', day: 'numeric', month: 'long' }).format(d);
  return s.charAt(0).toUpperCase() + s.slice(1);
}
