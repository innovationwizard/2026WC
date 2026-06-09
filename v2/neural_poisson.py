"""
Neural Poisson Model — FIFA World Cup 2026 Prediction System
=============================================================
Deep Poisson regression: predicts λ (expected goals) for each team
in a specific matchup. The ANN learns attacking and defensive
profiles from 30+ features, outputting Poisson rate parameters
that feed into Monte Carlo tournament simulation.

Architecture:
  Input → Dense(128,ReLU) → BN → Dropout(0.3)
        → Dense(64,ReLU)  → BN → Dropout(0.2)
        → Dense(32,ReLU)
        → Dense(1, Softplus)  →  λ (expected goals ≥ 0)

Loss: Poisson Negative Log-Likelihood
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks, regularizers
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.ensemble import HistGradientBoostingRegressor
import os
import json
import joblib


class NeuralPoissonModel:
    """
    Neural network that predicts expected goals (λ) via Poisson regression.
    
    The model takes team features as input and outputs λ ≥ 0,
    trained with Poisson negative log-likelihood loss.
    """

    def __init__(self, feature_names: list, seed: int = 42):
        self.feature_names = feature_names
        self.n_features = len(feature_names)
        self.seed = seed
        self.scaler = StandardScaler()
        self.model = None
        self.history = None
        self.feature_importance = None
        
        tf.random.set_seed(seed)
        np.random.seed(seed)

    def _build_model(self) -> keras.Model:
        """Build the neural network architecture."""
        inputs = keras.Input(shape=(self.n_features,), name='team_features')
        
        # Hidden layers with regularization
        x = layers.Dense(
            128, activation='relu',
            kernel_regularizer=regularizers.l2(1e-4),
            name='hidden_1'
        )(inputs)
        x = layers.BatchNormalization(name='bn_1')(x)
        x = layers.Dropout(0.3, name='dropout_1')(x)
        
        x = layers.Dense(
            64, activation='relu',
            kernel_regularizer=regularizers.l2(1e-4),
            name='hidden_2'
        )(x)
        x = layers.BatchNormalization(name='bn_2')(x)
        x = layers.Dropout(0.2, name='dropout_2')(x)
        
        x = layers.Dense(
            32, activation='relu',
            kernel_regularizer=regularizers.l2(1e-4),
            name='hidden_3'
        )(x)
        
        # Output: Softplus ensures λ > 0
        lambda_out = layers.Dense(
            1, activation='softplus', name='lambda_output'
        )(x)
        
        model = keras.Model(inputs=inputs, outputs=lambda_out, name='NeuralPoisson')
        
        # Poisson loss: -y*log(λ) + λ  (ignoring log(y!) constant)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-3),
            loss='poisson',
            metrics=['mae']
        )
        
        return model

    def fit(self, X: pd.DataFrame, y: pd.Series,
            epochs: int = 200, batch_size: int = 64,
            validation_split: float = 0.15,
            verbose: int = 0, compute_importance: bool = True) -> dict:
        """
        Train the model.
        
        Args:
            X: Feature matrix
            y: Target (goals scored)
            epochs: Max training epochs
            batch_size: Batch size
            validation_split: Fraction for validation
            verbose: Keras verbosity
            
        Returns:
            Training history dict
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X[self.feature_names].values)
        y_vals = y.values.astype(np.float32)
        
        # Build model
        self.model = self._build_model()
        
        # Callbacks
        cb = [
            callbacks.EarlyStopping(
                monitor='val_loss', patience=20,
                restore_best_weights=True, verbose=0
            ),
            callbacks.ReduceLROnPlateau(
                monitor='val_loss', factor=0.5,
                patience=8, min_lr=1e-6, verbose=0
            ),
        ]
        
        # Train
        self.history = self.model.fit(
            X_scaled, y_vals,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=cb,
            verbose=verbose
        )
        
        # Calculate feature importance via permutation (skippable — the ensemble
        # only needs it from one net, and it's the slow part of fit).
        if compute_importance:
            self._calculate_feature_importance(X_scaled, y_vals)
        
        result = {
            'final_loss': float(self.history.history['loss'][-1]),
            'final_val_loss': float(self.history.history['val_loss'][-1]),
            'best_val_loss': float(min(self.history.history['val_loss'])),
            'epochs_trained': len(self.history.history['loss']),
            'n_features': self.n_features,
            'n_samples': len(X),
        }
        
        print(f"Training complete: {result['epochs_trained']} epochs, "
              f"val_loss={result['best_val_loss']:.4f}")
        
        return result

    def predict_lambda(self, X: pd.DataFrame) -> np.ndarray:
        """Predict expected goals (λ). Eager call `model(x)` (float32) avoids the
        `model.predict()` tf.function retracing overhead — critical when called many
        times (ensemble × memoized Monte Carlo); makes single-row calls ~ms, not retraced."""
        X_scaled = self.scaler.transform(X[self.feature_names].values).astype('float32')
        return self.model(X_scaled, training=False).numpy().flatten()

    def predict_match(self, features_team_a: Dict[str, float],
                      features_team_b: Dict[str, float]) -> Tuple[float, float]:
        """
        Predict λ_A and λ_B for a specific match.
        
        Returns:
            (lambda_a, lambda_b): Expected goals for each team
        """
        df_a = pd.DataFrame([features_team_a])
        df_b = pd.DataFrame([features_team_b])
        
        lambda_a = self.predict_lambda(df_a)[0]
        lambda_b = self.predict_lambda(df_b)[0]
        
        return float(lambda_a), float(lambda_b)

    def _calculate_feature_importance(self, X_scaled: np.ndarray,
                                       y: np.ndarray, n_repeats: int = 10):
        """Calculate permutation feature importance."""
        baseline_loss = self.model.evaluate(X_scaled, y, verbose=0)[0]
        
        importances = {}
        for i, name in enumerate(self.feature_names):
            losses = []
            for _ in range(n_repeats):
                X_perm = X_scaled.copy()
                np.random.shuffle(X_perm[:, i])
                perm_loss = self.model.evaluate(X_perm, y, verbose=0)[0]
                losses.append(perm_loss)
            importances[name] = {
                'importance': float(np.mean(losses) - baseline_loss),
                'std': float(np.std(losses)),
            }
        
        # Sort by importance
        self.feature_importance = dict(
            sorted(importances.items(), key=lambda x: x[1]['importance'], reverse=True)
        )

    def get_feature_importance_df(self) -> pd.DataFrame:
        """Return feature importance as a DataFrame."""
        if self.feature_importance is None:
            return pd.DataFrame()
        
        rows = []
        for name, vals in self.feature_importance.items():
            rows.append({
                'feature': name,
                'importance': vals['importance'],
                'std': vals['std'],
            })
        return pd.DataFrame(rows)

    @staticmethod
    def weights_exist(path: str = 'output/model') -> bool:
        """True if a saved model exists at `path`."""
        return os.path.exists(os.path.join(path, 'neural_poisson.keras'))

    def save(self, path: str = 'output/model'):
        """Persist the trained model, scaler, feature list, and importances."""
        if self.model is None:
            raise RuntimeError("Nothing to save — model has not been trained.")
        os.makedirs(path, exist_ok=True)
        self.model.save(os.path.join(path, 'neural_poisson.keras'))
        joblib.dump(self.scaler, os.path.join(path, 'scaler.pkl'))
        with open(os.path.join(path, 'features.json'), 'w') as f:
            json.dump(self.feature_names, f)
        # Persist permutation importances so the cached-load path can still
        # emit the same diagnostics without retraining.
        if self.feature_importance is not None:
            with open(os.path.join(path, 'feature_importance.json'), 'w') as f:
                json.dump(self.feature_importance, f)

    def load(self, path: str = 'output/model'):
        """Load a previously saved model, scaler, features, and importances."""
        self.model = keras.models.load_model(os.path.join(path, 'neural_poisson.keras'))
        self.scaler = joblib.load(os.path.join(path, 'scaler.pkl'))
        with open(os.path.join(path, 'features.json')) as f:
            self.feature_names = json.load(f)
        self.n_features = len(self.feature_names)
        fi_path = os.path.join(path, 'feature_importance.json')
        if os.path.exists(fi_path):
            with open(fi_path) as f:
                self.feature_importance = json.load(f)
        return self

    def cross_validate(self, X: pd.DataFrame, y: pd.Series,
                       n_folds: int = 5) -> dict:
        """Run k-fold cross-validation and return metrics."""
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=self.seed)
        X_vals = X[self.feature_names].values
        y_vals = y.values.astype(np.float32)
        
        fold_losses = []
        fold_maes = []
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X_vals)):
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_vals[train_idx])
            X_val = scaler.transform(X_vals[val_idx])
            y_train, y_val = y_vals[train_idx], y_vals[val_idx]
            
            model = self._build_model()
            model.fit(
                X_train, y_train,
                epochs=150, batch_size=64,
                validation_data=(X_val, y_val),
                callbacks=[
                    callbacks.EarlyStopping(
                        monitor='val_loss', patience=15,
                        restore_best_weights=True, verbose=0
                    )
                ],
                verbose=0
            )
            
            loss, mae = model.evaluate(X_val, y_val, verbose=0)
            fold_losses.append(loss)
            fold_maes.append(mae)
            print(f"  Fold {fold+1}: loss={loss:.4f}, mae={mae:.4f}")
        
        result = {
            'mean_loss': float(np.mean(fold_losses)),
            'std_loss': float(np.std(fold_losses)),
            'mean_mae': float(np.mean(fold_maes)),
            'std_mae': float(np.std(fold_maes)),
        }
        print(f"CV Result: loss={result['mean_loss']:.4f}±{result['std_loss']:.4f}, "
              f"mae={result['mean_mae']:.4f}±{result['std_mae']:.4f}")
        
        return result


class EnsembleNeuralPoisson:
    """Ensemble of N NeuralPoissonModel instances (different seeds), averaging λ.

    Fixes the run-to-run training nondeterminism that makes single-net champion
    odds swing wildly (e.g. Brazil 23% ↔ 12% across retrains of the SAME code).
    Averaging N independently-trained nets stabilizes the predictions and tempers
    the lucky/unlucky extremes — the headline number stops depending on a seed.
    """

    def __init__(self, feature_names: list, n_models: int = 5, base_seed: int = 42):
        self.feature_names = feature_names
        self.n_features = len(feature_names)
        self.n_models = n_models
        self.models = [
            NeuralPoissonModel(feature_names, seed=base_seed + i) for i in range(n_models)
        ]
        self.feature_importance = None

    def cross_validate(self, X, y, n_folds: int = 5) -> dict:
        # One representative net's CV is enough; CV'ing the whole ensemble is overkill.
        return self.models[0].cross_validate(X, y, n_folds=n_folds)

    def fit(self, X, y, **kw) -> dict:
        for i, m in enumerate(self.models):
            print(f"  [ensemble {i + 1}/{self.n_models}] training...")
            m.fit(X, y, compute_importance=(i == 0), **kw)  # importance only on net 0
        self.feature_importance = self.models[0].feature_importance
        return {'n_models': self.n_models}

    def predict_lambda(self, X: pd.DataFrame) -> np.ndarray:
        preds = np.stack([m.predict_lambda(X) for m in self.models], axis=0)
        return preds.mean(axis=0)

    def get_feature_importance_df(self) -> pd.DataFrame:
        return self.models[0].get_feature_importance_df()


class GBTPoissonModel:
    """Gradient-boosted Poisson regressor (sklearn HistGradientBoosting, loss='poisson').

    A DIFFERENT model family than the neural net — trees split the feature space where
    the net interpolates it, so their errors are partly uncorrelated. That's exactly
    what makes blending the two into M3 (Conjunto) worthwhile. Trees are scale-invariant
    (no scaler needed) and the Poisson loss predicts a mean λ ≥ 0 directly.
    """

    def __init__(self, feature_names: list, seed: int = 42):
        self.feature_names = feature_names
        self.model = HistGradientBoostingRegressor(
            loss='poisson', max_iter=400, learning_rate=0.05,
            max_leaf_nodes=31, min_samples_leaf=40, l2_regularization=1.0,
            early_stopping=True, validation_fraction=0.15, random_state=seed,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series, **kw) -> dict:
        # **kw absorbs the net's epochs/batch_size args so it slots into the same call site.
        self.model.fit(X[self.feature_names].values, y.values.astype(float))
        return {'n_iter': int(self.model.n_iter_)}

    def predict_lambda(self, X: pd.DataFrame) -> np.ndarray:
        return np.clip(self.model.predict(X[self.feature_names].values), 0.01, None)


class ConjuntoModel:
    """M3 (Conjunto): blend of the M2 neural ensemble and the GBT Poisson model.

    λ_M3 = w·λ_net + (1-w)·λ_gbt. Two model families averaged → a distinct, more
    robust point forecaster than either alone (the lineup requires M3 ≠ M2). `w` is
    chosen by the held-out backtest, never by taste. Slots into the same pipeline
    interface as the net (fit / predict_lambda / get_feature_importance_df / cross_validate).
    """

    def __init__(self, feature_names: list, n_models: int = 50, base_seed: int = 42, w_net: float = 0.5):
        self.feature_names = feature_names
        self.net = EnsembleNeuralPoisson(feature_names, n_models=n_models, base_seed=base_seed)
        self.gbt = GBTPoissonModel(feature_names, seed=base_seed)
        self.w_net = w_net
        self.feature_importance = None

    def cross_validate(self, X, y, n_folds: int = 5) -> dict:
        return self.net.cross_validate(X, y, n_folds=n_folds)

    def fit(self, X, y, **kw) -> dict:
        self.net.fit(X, y, **kw)
        print("  [conjunto] training GBT member...")
        self.gbt.fit(X, y)
        self.feature_importance = self.net.feature_importance
        return {'w_net': self.w_net}

    def predict_lambda(self, X: pd.DataFrame) -> np.ndarray:
        return self.w_net * self.net.predict_lambda(X) + (1 - self.w_net) * self.gbt.predict_lambda(X)

    def get_feature_importance_df(self) -> pd.DataFrame:
        return self.net.get_feature_importance_df()


class EloBaselineModel:
    """
    Baseline model: Elo-only Poisson parameter estimation.
    Uses historical average goals and Elo difference to estimate λ.
    
    λ_team = avg_goals * (1 + α * elo_advantage / 400)
    
    This gives us a comparison point for the ANN.
    """

    GLOBAL_AVG_GOALS = 1.35  # Average goals per team per international match

    def __init__(self):
        self.alpha = 0.25  # Elo sensitivity

    def predict_match(self, elo_a: float, elo_b: float) -> Tuple[float, float]:
        """Predict λ for each team based on Elo difference."""
        elo_diff = elo_a - elo_b
        
        # Logistic-style adjustment
        expected_a = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))
        
        # Convert win probability to expected goals
        # Higher win probability → more goals scored, fewer conceded
        lambda_a = self.GLOBAL_AVG_GOALS * (0.5 + expected_a) 
        lambda_b = self.GLOBAL_AVG_GOALS * (0.5 + (1 - expected_a))
        
        # Clamp to reasonable range
        lambda_a = np.clip(lambda_a, 0.3, 4.0)
        lambda_b = np.clip(lambda_b, 0.3, 4.0)
        
        return float(lambda_a), float(lambda_b)
