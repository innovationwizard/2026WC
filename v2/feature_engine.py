"""
Feature Engineering Module — FIFA World Cup 2026 Prediction System
==================================================================
Vectorized implementation: Elo + 30 features computed via pandas rolling ops.
"""

import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, Tuple, Optional

# ─── STATIC DATA ─────────────────────────────────────────────────────────────

CONFEDERATION = {
    'Algeria': 'CAF', 'Argentina': 'CONMEBOL', 'Australia': 'AFC',
    'Austria': 'UEFA', 'Belgium': 'UEFA', 'Bosnia and Herzegovina': 'UEFA',
    'Brazil': 'CONMEBOL', 'Canada': 'CONCACAF', 'Cape Verde': 'CAF',
    'Colombia': 'CONMEBOL', 'Croatia': 'UEFA', 'Curaçao': 'CONCACAF',
    'Czech Republic': 'UEFA', 'DR Congo': 'CAF', 'Ecuador': 'CONMEBOL',
    'Egypt': 'CAF', 'England': 'UEFA', 'France': 'UEFA',
    'Germany': 'UEFA', 'Ghana': 'CAF', 'Haiti': 'CONCACAF',
    'Iran': 'AFC', 'Iraq': 'AFC', 'Ivory Coast': 'CAF',
    'Japan': 'AFC', 'Jordan': 'AFC', 'Mexico': 'CONCACAF',
    'Morocco': 'CAF', 'Netherlands': 'UEFA', 'New Zealand': 'OFC',
    'Norway': 'UEFA', 'Panama': 'CONCACAF', 'Paraguay': 'CONMEBOL',
    'Portugal': 'UEFA', 'Qatar': 'AFC', 'Saudi Arabia': 'AFC',
    'Scotland': 'UEFA', 'Senegal': 'CAF', 'South Africa': 'CAF',
    'South Korea': 'AFC', 'Spain': 'UEFA', 'Sweden': 'UEFA',
    'Switzerland': 'UEFA', 'Tunisia': 'CAF', 'Turkey': 'UEFA',
    'United States': 'CONCACAF', 'Uruguay': 'CONMEBOL', 'Uzbekistan': 'AFC',
}
HOST_COUNTRIES = {'United States', 'Mexico', 'Canada'}
WC_TEAMS = sorted(CONFEDERATION.keys())

WC_TITLES = {
    'Brazil': 5, 'Germany': 4, 'Argentina': 3, 'France': 2, 'Uruguay': 2,
    'England': 1, 'Spain': 1,
}
WC_APPEARANCES = {
    'Brazil': 22, 'Germany': 20, 'Argentina': 18, 'Mexico': 17, 'France': 16,
    'Spain': 16, 'England': 16, 'Uruguay': 14, 'Belgium': 14, 'South Korea': 11,
    'Japan': 7, 'Saudi Arabia': 7, 'Australia': 6, 'Netherlands': 11,
    'Switzerland': 12, 'Iran': 6, 'Colombia': 6, 'Ecuador': 4, 'Croatia': 6,
    'Portugal': 8, 'Tunisia': 6, 'Morocco': 6, 'Ghana': 4, 'Senegal': 3,
    'United States': 11, 'Canada': 2, 'Panama': 2, 'Egypt': 3, 'Algeria': 4,
    'Norway': 3, 'Scotland': 8, 'Paraguay': 8, 'Sweden': 12, 'Turkey': 2,
    'New Zealand': 2, 'Iraq': 1, 'Bosnia and Herzegovina': 1, 'Ivory Coast': 3,
    'South Africa': 3, 'Qatar': 1, 'Austria': 7, 'Jordan': 0, 'Cape Verde': 0,
    'Curaçao': 0, 'DR Congo': 1, 'Haiti': 1, 'Uzbekistan': 0, 'Czech Republic': 1,
}
GDP_PER_CAPITA = {
    'Algeria': 4000, 'Argentina': 13500, 'Australia': 65000, 'Austria': 56000,
    'Belgium': 51000, 'Bosnia and Herzegovina': 7500, 'Brazil': 9000,
    'Canada': 52000, 'Cape Verde': 3800, 'Colombia': 6600, 'Croatia': 19000,
    'Curaçao': 22000, 'Czech Republic': 27000, 'DR Congo': 580, 'Ecuador': 6200,
    'Egypt': 3900, 'England': 48000, 'France': 44000, 'Germany': 51000,
    'Ghana': 2400, 'Haiti': 1400, 'Iran': 4700, 'Iraq': 5200,
    'Ivory Coast': 2600, 'Japan': 34000, 'Jordan': 4500, 'Mexico': 11000,
    'Morocco': 3800, 'Netherlands': 57000, 'New Zealand': 48000, 'Norway': 82000,
    'Panama': 15000, 'Paraguay': 5800, 'Portugal': 25000, 'Qatar': 66000,
    'Saudi Arabia': 28000, 'Scotland': 48000, 'Senegal': 1600,
    'South Africa': 6000, 'South Korea': 33000, 'Spain': 31000, 'Sweden': 56000,
    'Switzerland': 93000, 'Tunisia': 3800, 'Turkey': 10000,
    'United States': 80000, 'Uruguay': 17000, 'Uzbekistan': 2100,
}
POPULATION = {
    'Algeria': 45, 'Argentina': 46, 'Australia': 26, 'Austria': 9,
    'Belgium': 12, 'Bosnia and Herzegovina': 3.2, 'Brazil': 215,
    'Canada': 40, 'Cape Verde': 0.6, 'Colombia': 52, 'Croatia': 3.9,
    'Curaçao': 0.15, 'Czech Republic': 10.7, 'DR Congo': 102, 'Ecuador': 18,
    'Egypt': 105, 'England': 57, 'France': 68, 'Germany': 84,
    'Ghana': 33, 'Haiti': 11.5, 'Iran': 87, 'Iraq': 43,
    'Ivory Coast': 28, 'Japan': 124, 'Jordan': 11, 'Mexico': 130,
    'Morocco': 37, 'Netherlands': 18, 'New Zealand': 5.2, 'Norway': 5.5,
    'Panama': 4.4, 'Paraguay': 7.3, 'Portugal': 10.3, 'Qatar': 2.9,
    'Saudi Arabia': 36, 'Scotland': 5.5, 'Senegal': 17,
    'South Africa': 60, 'South Korea': 52, 'Spain': 48, 'Sweden': 10.5,
    'Switzerland': 8.9, 'Tunisia': 12, 'Turkey': 85,
    'United States': 335, 'Uruguay': 3.5, 'Uzbekistan': 35,
}
SQUAD_MARKET_VALUE = {
    'England': 1680, 'France': 1520, 'Spain': 1410, 'Germany': 1100,
    'Brazil': 1050, 'Portugal': 980, 'Argentina': 850, 'Netherlands': 780,
    'Belgium': 620, 'Colombia': 450, 'Uruguay': 420, 'Croatia': 400,
    'Japan': 320, 'Morocco': 310, 'South Korea': 280, 'Senegal': 280,
    'United States': 270, 'Turkey': 260, 'Switzerland': 250, 'Norway': 240,
    'Austria': 230, 'Ivory Coast': 210, 'Ecuador': 200, 'Sweden': 200,
    'Mexico': 190, 'Egypt': 190, 'Scotland': 180, 'Czech Republic': 170,
    'Ghana': 150, 'Algeria': 140, 'Canada': 130, 'Australia': 120,
    'Bosnia and Herzegovina': 100, 'Paraguay': 95, 'Tunisia': 90,
    'DR Congo': 85, 'Saudi Arabia': 80, 'Iran': 55, 'Panama': 45,
    'Uzbekistan': 40, 'Qatar': 35, 'Cape Verde': 28, 'Iraq': 30,
    'Jordan': 15, 'New Zealand': 12, 'Haiti': 10, 'Curaçao': 8,
}


# ─── ELO SYSTEM (fast, single-pass) ─────────────────────────────────────────

def compute_elo(df: pd.DataFrame) -> Tuple[Dict[str, float], pd.DataFrame]:
    """Compute Elo ratings in a single pass. Returns final ratings and df with Elo columns."""
    K_MAP = {
        'FIFA World Cup': 60, 'Confederations Cup': 55,
        'Copa América': 50, 'UEFA Euro': 50, 'African Cup of Nations': 50,
        'AFC Asian Cup': 50, 'Gold Cup': 45, 'CONCACAF Nations League': 40,
        'UEFA Nations League': 45, 'FIFA World Cup qualification': 40,
        'UEFA Euro qualification': 40, 'African Cup of Nations qualification': 35,
        'AFC Asian Cup qualification': 35,
    }
    DEFAULT_K = 20

    ratings = defaultdict(lambda: 1500.0)
    elo_home_list = []
    elo_away_list = []

    for _, row in df.iterrows():
        h, a = row['home_team'], row['away_team']
        elo_h, elo_a = ratings[h], ratings[a]
        elo_home_list.append(elo_h)
        elo_away_list.append(elo_a)

        if pd.notna(row['home_score']):
            hs, as_ = int(row['home_score']), int(row['away_score'])
            exp_h = 1.0 / (1.0 + 10 ** ((elo_a - elo_h) / 400.0))
            actual_h = 1.0 if hs > as_ else (0.5 if hs == as_ else 0.0)
            gd = abs(hs - as_)
            g = 1.0 + (np.log(gd) if gd > 1 else 0.0)
            k = K_MAP.get(row['tournament'], DEFAULT_K)
            delta = k * g * (actual_h - exp_h)
            ratings[h] += delta
            ratings[a] -= delta

    df = df.copy()
    df['elo_home'] = elo_home_list
    df['elo_away'] = elo_away_list
    return dict(ratings), df


# ─── VECTORIZED FEATURE BUILDER ─────────────────────────────────────────────

def _normalize_team_view(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert match data to team-perspective rows.
    Each match produces 2 rows: one per team.
    Columns: date, team, opponent, goals_scored, goals_conceded, 
             result (W/D/L → 3/1/0), elo, opp_elo, tournament, neutral
    """
    scored = df[df['home_score'].notna()].copy()
    scored['home_score'] = scored['home_score'].astype(int)
    scored['away_score'] = scored['away_score'].astype(int)

    home = pd.DataFrame({
        'date': scored['date'], 'team': scored['home_team'],
        'opponent': scored['away_team'],
        'goals_scored': scored['home_score'], 'goals_conceded': scored['away_score'],
        'elo': scored['elo_home'], 'opp_elo': scored['elo_away'],
        'tournament': scored['tournament'],
        'neutral': scored['neutral'],
        'is_competitive': scored['tournament'] != 'Friendly',
    })
    away = pd.DataFrame({
        'date': scored['date'], 'team': scored['away_team'],
        'opponent': scored['home_team'],
        'goals_scored': scored['away_score'], 'goals_conceded': scored['home_score'],
        'elo': scored['elo_away'], 'opp_elo': scored['elo_home'],
        'tournament': scored['tournament'],
        'neutral': scored['neutral'],
        'is_competitive': scored['tournament'] != 'Friendly',
    })
    tv = pd.concat([home, away], ignore_index=True).sort_values('date').reset_index(drop=True)
    tv['goal_diff'] = tv['goals_scored'] - tv['goals_conceded']
    tv['result'] = np.where(tv['goals_scored'] > tv['goals_conceded'], 3,
                   np.where(tv['goals_scored'] == tv['goals_conceded'], 1, 0))
    tv['win'] = (tv['result'] == 3).astype(float)
    tv['draw'] = (tv['result'] == 1).astype(float)
    tv['clean_sheet'] = (tv['goals_conceded'] == 0).astype(float)
    return tv


def compute_rolling_features(tv: pd.DataFrame) -> pd.DataFrame:
    """Compute rolling statistics per team using groupby + rolling.

    v2 FIX (leakage): every rolling stat is `.shift(1)` so a match's features use
    only PRIOR matches — never the current match's own goals (which is the training
    label). The v1 baseline omitted the shift, leaking ~1/N of the label into
    `goals_scored_avg_*` and making the net over-rely on raw recent goals (the bias
    that buried low-scoring strong sides like Spain).
    """
    tv = tv.sort_values(['team', 'date']).reset_index(drop=True)

    for w in [5, 10, 20]:
        g = tv.groupby('team')
        tv[f'goals_scored_avg_{w}'] = g['goals_scored'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).mean())
        tv[f'goals_conceded_avg_{w}'] = g['goals_conceded'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).mean())
        tv[f'goal_diff_avg_{w}'] = g['goal_diff'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).mean())
        tv[f'win_rate_{w}'] = g['win'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).mean())
        tv[f'draw_rate_{w}'] = g['draw'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).mean())
        tv[f'points_per_game_{w}'] = g['result'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).mean())
        tv[f'clean_sheet_rate_{w}'] = g['clean_sheet'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).mean())
        tv[f'goals_scored_std_{w}'] = g['goals_scored'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=3).std())

    # Competitive match win rate (last 20 competitive) — also shifted (no current-match leak).
    tv_comp = tv[tv['is_competitive']].copy()
    comp_wr = tv_comp.groupby('team')['win'].transform(
        lambda x: x.shift(1).rolling(20, min_periods=3).mean())
    comp_ga = tv_comp.groupby('team')['goals_scored'].transform(
        lambda x: x.shift(1).rolling(20, min_periods=3).mean())
    tv['competitive_win_rate'] = np.nan
    tv['competitive_goals_avg'] = np.nan
    tv.loc[tv_comp.index, 'competitive_win_rate'] = comp_wr
    tv.loc[tv_comp.index, 'competitive_goals_avg'] = comp_ga
    tv['competitive_win_rate'] = tv.groupby('team')['competitive_win_rate'].ffill()
    tv['competitive_goals_avg'] = tv.groupby('team')['competitive_goals_avg'].ffill()

    # Neutral ground performance — shifted too.
    tv_neutral = tv[tv['neutral'] == True].copy()
    if len(tv_neutral) > 0:
        neut_wr = tv_neutral.groupby('team')['win'].transform(
            lambda x: x.shift(1).rolling(15, min_periods=2).mean())
        tv['neutral_win_rate'] = np.nan
        tv.loc[tv_neutral.index, 'neutral_win_rate'] = neut_wr
        tv['neutral_win_rate'] = tv.groupby('team')['neutral_win_rate'].ffill()
    else:
        tv['neutral_win_rate'] = 0.5

    return tv


def build_training_data(df_raw: pd.DataFrame, min_date: str = '2020-01-01', return_frame: bool = False):
    """
    Build training data (vectorized).
    Returns X, y, elo_ratings, team_view (for prediction functions).
    """
    df = df_raw.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    print("  Computing Elo ratings...")
    elo_ratings, df = compute_elo(df)

    print("  Building team-view dataset...")
    tv = _normalize_team_view(df)

    print("  Computing rolling features...")
    tv = compute_rolling_features(tv)

    # ── ASSEMBLE TRAINING ROWS ──
    # Each row = one team's stats at the time of a match + target = goals scored
    cutoff = pd.Timestamp(min_date)
    train = tv[tv['date'] >= cutoff].copy()

    # Rolling feature columns
    roll_cols = [c for c in train.columns if any(
        c.startswith(p) for p in ['goals_scored_avg', 'goals_conceded_avg',
        'goal_diff_avg', 'win_rate', 'draw_rate', 'points_per_game',
        'clean_sheet_rate', 'goals_scored_std', 'competitive_', 'neutral_']
    )]

    # Add static features per team
    train['elo_diff'] = train['elo'] - train['opp_elo']
    train['squad_market_value'] = train['team'].map(SQUAD_MARKET_VALUE).fillna(50)
    train['opp_squad_value'] = train['opponent'].map(SQUAD_MARKET_VALUE).fillna(50)
    train['squad_value_log'] = np.log1p(train['squad_market_value'])
    train['squad_value_diff'] = train['squad_market_value'] - train['opp_squad_value']
    train['gdp_log'] = train['team'].map(GDP_PER_CAPITA).fillna(10000).apply(np.log1p)
    train['population_log'] = train['team'].map(POPULATION).fillna(10).apply(lambda x: np.log1p(x * 1e6))
    train['wc_titles'] = train['team'].map(WC_TITLES).fillna(0)
    train['wc_appearances'] = train['team'].map(WC_APPEARANCES).fillna(0)
    train['is_host'] = train['team'].isin(HOST_COUNTRIES).astype(float)
    train['is_neutral'] = train['neutral'].astype(float)
    train['is_wc'] = train['tournament'].str.contains('World Cup', na=False).astype(float)

    # Confederation features
    train['conf'] = train['team'].map(CONFEDERATION).fillna('UEFA')
    train['opp_conf'] = train['opponent'].map(CONFEDERATION).fillna('UEFA')
    train['inter_confederation'] = (train['conf'] != train['opp_conf']).astype(float)
    for c in ['UEFA', 'CONMEBOL', 'CONCACAF', 'CAF', 'AFC', 'OFC']:
        train[f'conf_{c}'] = (train['conf'] == c).astype(float)

    # Confederation strength (avg Elo of WC teams in same conf)
    conf_strength = {}
    for c in set(CONFEDERATION.values()):
        teams_in_conf = [t for t, cc in CONFEDERATION.items() if cc == c]
        conf_strength[c] = np.mean([elo_ratings.get(t, 1500) for t in teams_in_conf])
    train['confederation_strength'] = train['conf'].map(conf_strength)

    # Feature columns
    feature_cols = (
        ['elo', 'elo_diff'] + roll_cols +
        ['squad_market_value', 'squad_value_log', 'squad_value_diff',
         'gdp_log', 'population_log', 'wc_titles', 'wc_appearances',
         'is_host', 'is_neutral', 'is_wc', 'inter_confederation',
         'confederation_strength'] +
        [f'conf_{c}' for c in ['UEFA', 'CONMEBOL', 'CONCACAF', 'CAF', 'AFC', 'OFC']]
    )

    # Drop rows with NaN in features
    X = train[feature_cols].copy()
    y = train['goals_scored'].copy()
    valid = X.notna().all(axis=1)
    X = X[valid].reset_index(drop=True)
    y = y[valid].reset_index(drop=True)

    # Remove constant columns
    non_const = [c for c in X.columns if X[c].std() > 1e-10]
    X = X[non_const]

    print(f"  Training samples: {len(X):,}  |  Features: {len(X.columns)}")

    if return_frame:
        # Full annotated frame (date/match identity + feature cols) for the backtest's
        # temporal split. Same row order/filter as X.
        keep = ['date', 'team', 'opponent', 'goals_scored', 'goals_conceded', 'elo', 'opp_elo']
        frame = train.loc[valid.values, keep].reset_index(drop=True)
        for c in X.columns:
            frame[c] = X[c].values
        return X, y, elo_ratings, tv, frame
    return X, y, elo_ratings, tv


def get_team_features_for_prediction(tv: pd.DataFrame, elo_ratings: dict,
                                      team: str, opponent: str) -> dict:
    """Get the most recent feature vector for a team (for WC prediction)."""
    team_rows = tv[tv['team'] == team]
    if len(team_rows) == 0:
        return _default_features(team, opponent, elo_ratings)

    last = team_rows.iloc[-1]
    features = {}

    # Elo
    features['elo'] = elo_ratings.get(team, 1500)
    features['elo_diff'] = elo_ratings.get(team, 1500) - elo_ratings.get(opponent, 1500)

    # Rolling stats (grab from last row)
    for col in tv.columns:
        if any(col.startswith(p) for p in [
            'goals_scored_avg', 'goals_conceded_avg', 'goal_diff_avg',
            'win_rate', 'draw_rate', 'points_per_game',
            'clean_sheet_rate', 'goals_scored_std',
            'competitive_', 'neutral_'
        ]):
            val = last.get(col, np.nan)
            features[col] = val if pd.notna(val) else 0.5

    # Static
    features['squad_market_value'] = SQUAD_MARKET_VALUE.get(team, 50)
    features['squad_value_log'] = np.log1p(features['squad_market_value'])
    features['squad_value_diff'] = SQUAD_MARKET_VALUE.get(team, 50) - SQUAD_MARKET_VALUE.get(opponent, 50)
    features['gdp_log'] = np.log1p(GDP_PER_CAPITA.get(team, 10000))
    features['population_log'] = np.log1p(POPULATION.get(team, 10) * 1e6)
    features['wc_titles'] = WC_TITLES.get(team, 0)
    features['wc_appearances'] = WC_APPEARANCES.get(team, 0)
    features['is_host'] = 1.0 if team in HOST_COUNTRIES else 0.0
    features['is_neutral'] = 1.0
    features['is_wc'] = 1.0
    conf = CONFEDERATION.get(team, 'UEFA')
    opp_conf = CONFEDERATION.get(opponent, 'UEFA')
    features['inter_confederation'] = 1.0 if conf != opp_conf else 0.0
    for c in ['UEFA', 'CONMEBOL', 'CONCACAF', 'CAF', 'AFC', 'OFC']:
        features[f'conf_{c}'] = 1.0 if conf == c else 0.0

    conf_teams = [t for t, cc in CONFEDERATION.items() if cc == conf]
    features['confederation_strength'] = np.mean([elo_ratings.get(t, 1500) for t in conf_teams])

    return features


def _default_features(team, opponent, elo_ratings):
    """Fallback feature vector for teams with insufficient history."""
    f = {'elo': elo_ratings.get(team, 1500),
         'elo_diff': elo_ratings.get(team, 1500) - elo_ratings.get(opponent, 1500)}
    for w in [5, 10, 20]:
        for k in ['goals_scored_avg', 'goals_conceded_avg', 'goal_diff_avg',
                   'win_rate', 'draw_rate', 'points_per_game', 'clean_sheet_rate',
                   'goals_scored_std']:
            f[f'{k}_{w}'] = 0.5 if 'rate' in k else 1.0
    f['competitive_win_rate'] = 0.5
    f['competitive_goals_avg'] = 1.0
    f['neutral_win_rate'] = 0.5
    f['squad_market_value'] = SQUAD_MARKET_VALUE.get(team, 50)
    f['squad_value_log'] = np.log1p(f['squad_market_value'])
    f['squad_value_diff'] = SQUAD_MARKET_VALUE.get(team, 50) - SQUAD_MARKET_VALUE.get(opponent, 50)
    f['gdp_log'] = np.log1p(GDP_PER_CAPITA.get(team, 10000))
    f['population_log'] = np.log1p(POPULATION.get(team, 10) * 1e6)
    f['wc_titles'] = WC_TITLES.get(team, 0)
    f['wc_appearances'] = WC_APPEARANCES.get(team, 0)
    f['is_host'] = 1.0 if team in HOST_COUNTRIES else 0.0
    f['is_neutral'] = 1.0
    f['is_wc'] = 1.0
    conf = CONFEDERATION.get(team, 'UEFA')
    opp_conf = CONFEDERATION.get(opponent, 'UEFA')
    f['inter_confederation'] = 1.0 if conf != opp_conf else 0.0
    for c in ['UEFA', 'CONMEBOL', 'CONCACAF', 'CAF', 'AFC', 'OFC']:
        f[f'conf_{c}'] = 1.0 if conf == c else 0.0
    f['confederation_strength'] = 1500.0
    return f
