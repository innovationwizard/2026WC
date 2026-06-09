"""
FIFA World Cup 2026 — AI Prediction System
==========================================
python main.py  →  predictions.json + diagnostics
"""
import sys, os, json, time
import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import (
    build_training_data, get_team_features_for_prediction,
    WC_TEAMS, CONFEDERATION, HOST_COUNTRIES, SQUAD_MARKET_VALUE,
    GDP_PER_CAPITA, POPULATION, WC_TITLES, WC_APPEARANCES
)
from neural_poisson import NeuralPoissonModel, EloBaselineModel, EnsembleNeuralPoisson
from monte_carlo import run_monte_carlo, GROUPS

N_SIMULATIONS = 10_000

def main():
    t0 = time.time()
    print("="*70)
    print("  FIFA WORLD CUP 2026 — AI PREDICTION SYSTEM")
    print("  Neural Poisson + Monte Carlo (10K simulations)")
    print("="*70)

    # ── 1. Load data ──
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'results.csv')
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), 'results.csv')
    if not os.path.exists(csv_path):
        csv_path = '/home/claude/results.csv'
    print(f"\n[1/6] Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')  # bad dates → NaT (caught by P0)
    print(f"  {len(df):,} total rows")

    # ── P0: data integrity (Dirty George guard) — fail loud before any modeling ──
    from data_integrity import audit_load
    _report = audit_load(df, WC_TEAMS, today=pd.Timestamp.today().normalize(),
                         squad_values=SQUAD_MARKET_VALUE)
    _report.summary()
    _report.assert_ok()

    # ── 2. Feature engineering ──
    print("\n[2/6] Engineering features...")
    X, y, elo_ratings, tv = build_training_data(df, min_date='2020-01-01')

    feature_names = sorted(X.columns.tolist())
    print(f"  Goals distribution: mean={y.mean():.2f}, std={y.std():.2f}")

    sorted_elo = sorted(
        {t: elo_ratings.get(t, 1500) for t in WC_TEAMS}.items(),
        key=lambda x: x[1], reverse=True
    )
    print("\n  Top 15 WC teams by Elo:")
    for i, (team, elo) in enumerate(sorted_elo[:15]):
        print(f"    {i+1:2d}. {team:25s} {elo:.0f}")

    # ── 3. Train (or load) Neural Poisson ──
    print("\n[3/6] Neural Poisson Model...")
    out_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(out_dir, exist_ok=True)
    model_dir = os.path.join(out_dir, 'model')
    cv_path = os.path.join(model_dir, 'cv.json')

    # v2: ENSEMBLE of N nets (different seeds), averaging λ — fixes run-to-run
    # training nondeterminism (single-net champion odds swing wildly). Always
    # retrains fresh (no cache) while we iterate on the model.
    N_ENSEMBLE = 5
    model = EnsembleNeuralPoisson(feature_names=feature_names, n_models=N_ENSEMBLE, base_seed=42)

    print("  Cross-validating (5-fold)...")
    cv = model.cross_validate(X, y, n_folds=5)

    print(f"  Training ensemble of {N_ENSEMBLE} nets (stability fix)...")
    tr = model.fit(X, y, epochs=300, batch_size=64, verbose=0)

    imp = model.get_feature_importance_df()
    print("\n  Top 15 features:")
    for _, r in imp.head(15).iterrows():
        bar = '█' * max(1, int(r['importance'] * 500))
        print(f"    {r['feature']:35s} {r['importance']:.4f} {bar}")

    # ── 4. Prediction functions ──
    print("\n[4/6] Building prediction functions...")

    # Base λ for a matchup depends only on (team_a, team_b) — the model and
    # features are fixed, so it's identical across all 10K simulations. Without
    # caching, Monte Carlo issues ~2M single-row Keras predict() calls (hours of
    # framework overhead). Memoize the base λ per ordered matchup; the stage
    # multiplier is applied on top, so results are mathematically unchanged.
    _lambda_cache = {}
    def neural_predict(team_a, team_b, stage='group'):
        key = (team_a, team_b)
        if key not in _lambda_cache:
            fa = get_team_features_for_prediction(tv, elo_ratings, team_a, team_b)
            fb = get_team_features_for_prediction(tv, elo_ratings, team_b, team_a)
            for f in feature_names:
                fa.setdefault(f, 0.0)
                fb.setdefault(f, 0.0)
            da = pd.DataFrame([fa])[feature_names]
            db = pd.DataFrame([fb])[feature_names]
            _lambda_cache[key] = (float(model.predict_lambda(da)[0]),
                                  float(model.predict_lambda(db)[0]))
        la, lb = _lambda_cache[key]
        if stage in ('QF', 'SF', 'Final'):
            la *= 0.90; lb *= 0.90
        elif stage in ('R32', 'R16'):
            la *= 0.95; lb *= 0.95
        return float(la), float(lb)

    baseline = EloBaselineModel()
    def elo_predict(team_a, team_b, stage='group'):
        return baseline.predict_match(elo_ratings.get(team_a, 1500),
                                       elo_ratings.get(team_b, 1500))

    # ── 5. Monte Carlo ──
    print("\n[5/6] Running Monte Carlo simulations...")
    nr = run_monte_carlo(neural_predict, N_SIMULATIONS, seed=42, label="Neural Poisson")
    er = run_monte_carlo(elo_predict, N_SIMULATIONS, seed=42, label="Elo Baseline")

    # ── 6. Diagnostics ──
    print("\n[6/6] Diagnostics...")

    disagreements = []
    for team in WC_TEAMS:
        np_c = nr['team_probs'][team]['champion']
        el_c = er['team_probs'][team]['champion']
        d = np_c - el_c
        if abs(d) > 0.005:
            disagreements.append({
                'team': team,
                'neural_poisson': round(np_c*100, 2),
                'elo_baseline': round(el_c*100, 2),
                'difference': round(d*100, 2),
                'direction': 'ANN favors' if d > 0 else 'Elo favors',
            })
    disagreements.sort(key=lambda x: abs(x['difference']), reverse=True)

    print("\n  Model Disagreements:")
    for d in disagreements[:10]:
        arrow = '↑' if d['difference'] > 0 else '↓'
        print(f"    {d['team']:25s} Neural:{d['neural_poisson']:5.1f}%  "
              f"Elo:{d['elo_baseline']:5.1f}%  {arrow}{abs(d['difference']):.1f}pp")

    # Upset radar
    upsets = []
    for key, data in nr['match_predictions'].items():
        ea = elo_ratings.get(data['team_a'], 1500)
        eb = elo_ratings.get(data['team_b'], 1500)
        if ea > eb:
            up = data['prob_win_b']; ut = data['team_b']; fav = data['team_a']
        else:
            up = data['prob_win_a']; ut = data['team_a']; fav = data['team_b']
        if up > 0.10:
            upsets.append({'match': key, 'upset_team': ut, 'favored': fav,
                          'upset_prob': round(up*100, 1)})
    upsets.sort(key=lambda x: x['upset_prob'], reverse=True)

    # ── Save ──
    predictions = {
        'metadata': {
            'model': 'Neural Poisson + Monte Carlo',
            'n_simulations': N_SIMULATIONS,
            'n_features': len(feature_names),
            'training_samples': len(X),
            'training_period': '2020-2026',
            'cv_loss': cv['mean_loss'], 'cv_mae': cv['mean_mae'],
        },
        'team_probabilities': nr['team_probs'],
        'group_predictions': nr['group_predictions'],
        'match_predictions': nr['match_predictions'],
        'elo_ratings': {t: round(elo_ratings.get(t, 1500), 1) for t in WC_TEAMS},
        'elo_baseline': er['team_probs'],
        'disagreements': disagreements,
        'upsets': upsets[:15],
        'feature_importance': imp.head(20).to_dict('records'),
        'groups': {g: list(t) for g, t in GROUPS.items()},
        'squad_values': SQUAD_MARKET_VALUE,
        'feature_names': feature_names,
    }

    path = os.path.join(out_dir, 'predictions.json')
    with open(path, 'w') as f:
        json.dump(predictions, f, indent=2, default=str)

    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"  DONE — {elapsed:.0f}s  →  {path}")
    print(f"{'='*70}")
    return predictions

if __name__ == '__main__':
    main()
