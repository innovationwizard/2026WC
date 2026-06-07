"""
HTML Report Generator — FIFA World Cup 2026 Predictions
========================================================
Reads predictions.json → generates a self-contained HTML file.
Spanish labels. No external dependencies in the HTML.

Usage:
    python generate_html.py
    # or:
    python generate_html.py path/to/predictions.json
"""

import json, sys, os

def generate_html(predictions: dict, output_path: str = None):
    """Generate self-contained HTML from predictions dict."""

    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), 'output', 'wc2026_predicciones.html')

    tp = predictions['team_probabilities']
    gp = predictions['group_predictions']
    mp = predictions['match_predictions']
    elo = predictions['elo_ratings']
    groups = predictions['groups']
    meta = predictions['metadata']
    disagreements = predictions.get('disagreements', [])
    upsets = predictions.get('upsets', [])
    feat_imp = predictions.get('feature_importance', [])
    elo_baseline = predictions.get('elo_baseline', {})
    squad_vals = predictions.get('squad_values', {})

    # Sort teams by champion probability
    sorted_teams = sorted(tp.items(), key=lambda x: x[1]['champion'], reverse=True)

    # ── Build champion bar chart data ──
    champ_bars = ""
    for i, (team, probs) in enumerate(sorted_teams[:20]):
        pct = probs['champion'] * 100
        color = '#d4af37' if i == 0 else ('#c0c0c0' if i == 1 else ('#cd7f32' if i == 2 else '#4a90d9'))
        champ_bars += f"""
        <div class="bar-row">
          <span class="bar-label">{i+1}. {team}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct*3}%;background:{color}"></div>
          </div>
          <span class="bar-value">{pct:.1f}%</span>
        </div>"""

    # ── Build group tables ──
    group_html = ""
    for g in sorted(groups.keys()):
        teams = groups[g]
        rows = ""
        gw = gp[g]['winner_probs']
        gr = gp[g]['runner_probs']
        for team in sorted(teams, key=lambda t: gw.get(t, 0) + gr.get(t, 0), reverse=True):
            adv = (gw.get(team, 0) + gr.get(team, 0)) * 100
            champ = tp[team]['champion'] * 100
            e = elo.get(team, 1500)
            sv = squad_vals.get(team, 0)
            rows += f"""
            <tr>
              <td class="team-name">{team}</td>
              <td>{e:.0f}</td>
              <td>€{sv}M</td>
              <td><strong>{adv:.0f}%</strong></td>
              <td>{champ:.1f}%</td>
            </tr>"""

        # Group matches
        match_rows = ""
        for key, data in mp.items():
            if data.get('group') == g:
                ta, tb = data['team_a'], data['team_b']
                pa = data['prob_win_a'] * 100
                pd_ = data['prob_draw'] * 100
                pb = data['prob_win_b'] * 100
                la = data.get('lambda_a', 0)
                lb = data.get('lambda_b', 0)
                match_rows += f"""
                <tr>
                  <td>{ta}</td>
                  <td class="prob-w">{pa:.0f}%</td>
                  <td class="prob-d">{pd_:.0f}%</td>
                  <td class="prob-w">{pb:.0f}%</td>
                  <td>{tb}</td>
                  <td class="xg">{la:.2f} - {lb:.2f}</td>
                </tr>"""

        group_html += f"""
        <div class="group-card">
          <h3>Grupo {g}</h3>
          <table class="group-table">
            <thead><tr><th>Selección</th><th>Elo</th><th>Valor</th><th>Avanza</th><th>Campeón</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
          <h4>Partidos</h4>
          <table class="match-table">
            <thead><tr><th>Local</th><th>G</th><th>E</th><th>G</th><th>Visitante</th><th>xG</th></tr></thead>
            <tbody>{match_rows}</tbody>
          </table>
        </div>"""

    # ── Stage probabilities table (top 16) ──
    stage_rows = ""
    for i, (team, probs) in enumerate(sorted_teams[:16]):
        stage_rows += f"""
        <tr>
          <td>{i+1}</td><td class="team-name">{team}</td>
          <td>{probs.get('group_advance',0)*100:.0f}%</td>
          <td>{probs.get('r32',0)*100:.0f}%</td>
          <td>{probs.get('r16',0)*100:.0f}%</td>
          <td>{probs.get('quarterfinal',0)*100:.0f}%</td>
          <td>{probs.get('semifinal',0)*100:.0f}%</td>
          <td>{probs.get('finalist',0)*100:.0f}%</td>
          <td><strong>{probs['champion']*100:.1f}%</strong></td>
        </tr>"""

    # ── Disagreements ──
    disagree_rows = ""
    for d in disagreements[:10]:
        arrow = '↑' if d['difference'] > 0 else '↓'
        cl = 'ann-up' if d['difference'] > 0 else 'ann-down'
        disagree_rows += f"""
        <tr class="{cl}">
          <td class="team-name">{d['team']}</td>
          <td>{d['neural_poisson']:.1f}%</td>
          <td>{d['elo_baseline']:.1f}%</td>
          <td>{arrow} {abs(d['difference']):.1f}pp</td>
        </tr>"""

    # ── Feature importance ──
    feat_rows = ""
    if feat_imp:
        max_imp = max(f['importance'] for f in feat_imp) if feat_imp else 1
        for f in feat_imp[:15]:
            w = (f['importance'] / max_imp) * 100 if max_imp > 0 else 0
            feat_rows += f"""
            <div class="feat-row">
              <span class="feat-name">{f['feature']}</span>
              <div class="feat-track"><div class="feat-bar" style="width:{w}%"></div></div>
              <span class="feat-val">{f['importance']:.4f}</span>
            </div>"""

    # ── Upset radar ──
    upset_rows = ""
    for u in upsets[:10]:
        upset_rows += f"""
        <tr>
          <td>{u['match']}</td>
          <td class="team-name">{u['upset_team']}</td>
          <td><strong>{u['upset_prob']}%</strong></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FIFA World Cup 2026 — Predicción IA</title>
<style>
  :root {{
    --bg: #0a0e17; --card: #111827; --border: #1e293b;
    --gold: #d4af37; --silver: #94a3b8; --accent: #3b82f6;
    --text: #e2e8f0; --muted: #64748b; --green: #22c55e; --red: #ef4444;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',system-ui,sans-serif; line-height:1.6; padding:1rem; }}
  .container {{ max-width:1200px; margin:0 auto; }}
  h1 {{ text-align:center; font-size:2rem; color:var(--gold); margin:1rem 0 0.25rem; }}
  h2 {{ color:var(--accent); border-bottom:2px solid var(--border); padding-bottom:0.5rem; margin:2rem 0 1rem; font-size:1.4rem; }}
  h3 {{ color:var(--gold); margin-bottom:0.5rem; font-size:1.1rem; }}
  h4 {{ color:var(--muted); margin:0.75rem 0 0.25rem; font-size:0.9rem; }}
  .subtitle {{ text-align:center; color:var(--muted); margin-bottom:1.5rem; font-size:0.9rem; }}
  .meta-bar {{ display:flex; justify-content:center; gap:2rem; flex-wrap:wrap; background:var(--card); border:1px solid var(--border); border-radius:8px; padding:0.75rem; margin-bottom:2rem; font-size:0.85rem; color:var(--muted); }}
  .meta-bar span {{ white-space:nowrap; }}
  .meta-bar strong {{ color:var(--text); }}

  /* Bar chart */
  .bar-row {{ display:flex; align-items:center; margin:3px 0; }}
  .bar-label {{ width:180px; font-size:0.85rem; text-align:right; padding-right:10px; }}
  .bar-track {{ flex:1; height:22px; background:var(--card); border-radius:4px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:4px; transition:width 0.5s; min-width:2px; }}
  .bar-value {{ width:55px; text-align:right; font-size:0.85rem; font-weight:700; padding-left:8px; }}

  /* Groups */
  .groups-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:1rem; }}
  .group-card {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1rem; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.8rem; }}
  th {{ background:#1e293b; color:var(--muted); padding:4px 6px; text-align:left; font-weight:600; text-transform:uppercase; font-size:0.7rem; }}
  td {{ padding:4px 6px; border-bottom:1px solid var(--border); }}
  .team-name {{ font-weight:600; }}
  .prob-w {{ color:var(--green); font-weight:600; }}
  .prob-d {{ color:var(--muted); }}
  .xg {{ color:var(--accent); font-family:monospace; }}

  /* Stage table */
  .stage-table {{ font-size:0.8rem; }}
  .stage-table td {{ text-align:center; }}
  .stage-table td:nth-child(2) {{ text-align:left; }}
  .stage-table tr:nth-child(-n+3) {{ background:rgba(212,175,55,0.08); }}

  /* Disagreements */
  .ann-up {{ background:rgba(34,197,94,0.08); }}
  .ann-down {{ background:rgba(239,68,68,0.08); }}

  /* Feature importance */
  .feat-row {{ display:flex; align-items:center; margin:2px 0; }}
  .feat-name {{ width:220px; font-size:0.75rem; font-family:monospace; text-align:right; padding-right:8px; color:var(--muted); }}
  .feat-track {{ flex:1; height:14px; background:#1e293b; border-radius:3px; overflow:hidden; }}
  .feat-bar {{ height:100%; background:var(--accent); border-radius:3px; }}
  .feat-val {{ width:60px; font-size:0.75rem; font-family:monospace; text-align:right; padding-left:6px; }}

  /* Methodology */
  .method-box {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1.25rem; font-size:0.85rem; }}
  .method-box p {{ margin-bottom:0.75rem; }}
  .method-box code {{ background:#1e293b; padding:2px 6px; border-radius:3px; font-size:0.8rem; }}
  .arch-diagram {{ font-family:monospace; font-size:0.75rem; background:#0f172a; padding:1rem; border-radius:6px; overflow-x:auto; white-space:pre; line-height:1.4; color:var(--accent); margin:0.75rem 0; }}

  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
  @media(max-width:768px) {{ .two-col,.groups-grid {{ grid-template-columns:1fr; }} .bar-label {{ width:120px; }} }}

  footer {{ text-align:center; color:var(--muted); margin-top:3rem; padding:1rem; font-size:0.75rem; border-top:1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">

<h1>⚽ Copa Mundial FIFA 2026</h1>
<p class="subtitle">Predicción basada en Inteligencia Artificial — Red Neuronal Poisson + Simulación Monte Carlo</p>

<div class="meta-bar">
  <span>🧠 Modelo: <strong>Neural Poisson (ANN)</strong></span>
  <span>🔁 Simulaciones: <strong>{meta['n_simulations']:,}</strong></span>
  <span>📊 Variables: <strong>{meta['n_features']}</strong></span>
  <span>📈 Datos de entrenamiento: <strong>{meta['training_samples']:,}</strong> partidos</span>
  <span>📅 Período: <strong>{meta['training_period']}</strong></span>
</div>

<h2>🏆 Probabilidad de ser Campeón</h2>
<div>{champ_bars}</div>

<h2>📊 Probabilidad por Etapa (Top 16)</h2>
<table class="stage-table">
<thead><tr><th>#</th><th>Selección</th><th>Grupos</th><th>R32</th><th>R16</th><th>Cuartos</th><th>Semis</th><th>Final</th><th>Campeón</th></tr></thead>
<tbody>{stage_rows}</tbody>
</table>

<h2>📋 Predicciones por Grupo</h2>
<div class="groups-grid">{group_html}</div>

<h2>🔬 Análisis del Modelo</h2>
<div class="two-col">
  <div>
    <h3>Discrepancias: Red Neuronal vs. Elo Puro</h3>
    <p style="font-size:0.8rem;color:var(--muted);margin-bottom:0.5rem;">
      Donde la red neuronal ve algo que el Elo puro no captura.
    </p>
    <table>
    <thead><tr><th>Selección</th><th>ANN</th><th>Elo</th><th>Δ</th></tr></thead>
    <tbody>{disagree_rows}</tbody>
    </table>
  </div>
  <div>
    <h3>Importancia de Variables</h3>
    <p style="font-size:0.8rem;color:var(--muted);margin-bottom:0.5rem;">
      Variables que más contribuyen a la predicción (importancia por permutación).
    </p>
    {feat_rows}
  </div>
</div>

<h2>⚡ Radar de Sorpresas</h2>
<p style="font-size:0.85rem;color:var(--muted);margin-bottom:0.5rem;">
  Partidos donde el equipo con menor Elo tiene mayor probabilidad de ganar.
</p>
<table>
<thead><tr><th>Partido</th><th>Sorpresa</th><th>Probabilidad</th></tr></thead>
<tbody>{upset_rows}</tbody>
</table>

<h2>🧠 Metodología</h2>
<div class="method-box">
  <p><strong>Arquitectura:</strong> Red neuronal de regresión Poisson (Deep Poisson Regression). En lugar de predecir
  ganar/empatar/perder, la red predice <code>λ_A</code> y <code>λ_B</code> — los goles esperados de cada selección en cada
  enfrentamiento específico. Estos parámetros alimentan distribuciones de Poisson dentro de la simulación Monte Carlo.</p>

  <div class="arch-diagram">INPUT ({meta['n_features']} variables por equipo):
├── Elo, diferencia Elo, ranking FIFA
├── Forma reciente (5/10/20 partidos): goles, victorias, portería invicta
├── Rendimiento en partidos competitivos vs amistosos
├── Rendimiento en terreno neutral
├── Valor de mercado del plantel (Transfermarkt)
├── Diferencia de valor de mercado
├── PIB per cápita, población (infraestructura deportiva)
├── Títulos mundiales, apariciones históricas
├── Ventaja de país sede (USA/MEX/CAN)
├── Confederación + fuerza de confederación
└── Tipo de enfrentamiento (inter vs intra-confederación)

CAPAS OCULTAS:
├── Dense(128, ReLU) → BatchNorm → Dropout(0.3)
├── Dense(64, ReLU)  → BatchNorm → Dropout(0.2)
└── Dense(32, ReLU)

SALIDA:
└── Dense(1, Softplus) → λ (goles esperados ≥ 0)

LOSS: Poisson Negative Log-Likelihood
  </div>

  <p><strong>Simulación Monte Carlo:</strong> Para cada uno de los {meta['n_simulations']:,} torneos simulados, cada
  partido se resuelve muestreando goles de <code>Poisson(λ)</code>. Esto produce marcadores reales
  (2-1, 0-0, 3-2), no solo resultados. Los desempates de grupo se resuelven correctamente por diferencia de goles
  y goles a favor.</p>

  <p><strong>Validación cruzada (5-fold):</strong> Pérdida Poisson = <code>{meta['cv_loss']:.4f}</code>,
  MAE = <code>{meta['cv_mae']:.4f}</code> goles.</p>

  <p><strong>Comparación dual:</strong> Se ejecutan dos modelos en paralelo — la red neuronal (47 variables) y
  un baseline de Elo puro. Las discrepancias entre ambos revelan dónde las variables adicionales
  (valor de mercado, forma reciente, historial mundialista) cambian la predicción respecto al Elo solo.</p>
</div>

<footer>
  Modelo construido por el Director de IA, Grupo Orión — Junio 2026<br>
  {meta['n_features']} variables · {meta['training_samples']:,} partidos · {meta['n_simulations']:,} simulaciones Monte Carlo<br>
  Código reproducible: <code>python main.py</code> → predicciones completas
</footer>

</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML generated: {output_path}")
    return output_path


if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), 'output', 'predictions.json')
    with open(json_path) as f:
        predictions = json.load(f)
    generate_html(predictions)
