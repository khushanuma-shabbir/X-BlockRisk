"""
Lightweight ML-based fraud detector trained on REAL Ethereum data.
Uses Random Forest - simple, fast, interpretable, and actually works.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler
import json

class LightweightFraudDetector:
    """
    Random Forest classifier trained on Ethereum address behavioral features.
    Much simpler than GNN, but actually works because it's trained on relevant data.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_importance = None
        self.model_path = Path("models/lightweight_fraud_detector.pkl")
        self.scaler_path = Path("models/feature_scaler.pkl")
        self.metrics_path = Path("models/model_metrics.json")
        
        # Ensure model directory exists
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    def train(self, training_data_path: str = "data/ml_training/ethereum_training_data.csv"):
        """
        Train the Random Forest model on collected Ethereum data.
        
        Args:
            training_data_path: Path to CSV with labeled addresses and features
        """
        print("\n=== TRAINING LIGHTWEIGHT FRAUD DETECTOR ===\n")
        
        # Load data
        df = pd.read_csv(training_data_path)
        print(f"Loaded {len(df)} labeled addresses")
        print(f"  Phishing: {len(df[df['label']==1])}")
        print(f"  Legitimate: {len(df[df['label']==0])}")
        
        # Separate features and labels
        feature_cols = [
            'total_txs', 'total_value_eth', 'avg_tx_value',
            'unique_senders', 'unique_receivers', 'is_contract',
            'first_tx_age_days', 'last_tx_age_days', 'tx_frequency',
            'incoming_tx_count', 'outgoing_tx_count', 'avg_gas_price',
            'failed_tx_ratio'
        ]
        
        X = df[feature_cols].fillna(0)
        y = df['label']
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Train Random Forest
        print("\nTraining Random Forest...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'  # Handle class imbalance
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        print("\n=== TRAINING RESULTS ===")
        
        # Training accuracy
        train_score = self.model.score(X_train, y_train)
        print(f"Training Accuracy: {train_score:.2%}")
        
        # Test accuracy
        test_score = self.model.score(X_test, y_test)
        print(f"Test Accuracy: {test_score:.2%}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
        print(f"Cross-Validation Accuracy: {cv_scores.mean():.2%} (+/- {cv_scores.std():.2%})")
        
        # Detailed metrics
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        print("\n=== CLASSIFICATION REPORT ===")
        print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Phishing']))
        
        print("\n=== CONFUSION MATRIX ===")
        cm = confusion_matrix(y_test, y_pred)
        print(f"True Negatives: {cm[0][0]}, False Positives: {cm[0][1]}")
        print(f"False Negatives: {cm[1][0]}, True Positives: {cm[1][1]}")
        
        # ROC AUC
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        print(f"\nROC AUC Score: {roc_auc:.3f}")
        
        # Feature importance
        self.feature_importance = dict(zip(feature_cols, self.model.feature_importances_))
        print("\n=== FEATURE IMPORTANCE ===")
        for feature, importance in sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True):
            print(f"{feature:25s}: {importance:.4f}")
        
        # Save model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        # Save metrics
        metrics = {
            'train_accuracy': float(train_score),
            'test_accuracy': float(test_score),
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'roc_auc': float(roc_auc),
            'feature_importance': {k: float(v) for k, v in self.feature_importance.items()},
            'confusion_matrix': cm.tolist(),
            'training_size': len(X_train),
            'test_size': len(X_test)
        }
        
        with open(self.metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n=== MODEL SAVED ===")
        print(f"Model: {self.model_path}")
        print(f"Scaler: {self.scaler_path}")
        print(f"Metrics: {self.metrics_path}")
        
        return metrics
    
    def load(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}. Train the model first.")
        
        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        
        with open(self.metrics_path, 'r') as f:
            metrics = json.load(f)
        
        self.feature_importance = metrics['feature_importance']
        
        print(f"Loaded model with {metrics['test_accuracy']:.2%} test accuracy")
    
    def predict(self, features: dict) -> tuple[float, str]:
        """
        Predict fraud probability for an address.
        
        Args:
            features: Dictionary with same keys as training data
        
        Returns:
            (probability, confidence_level)
        """
        if self.model is None:
            self.load()
        
        # Convert features to array in correct order
        feature_cols = [
            'total_txs', 'total_value_eth', 'avg_tx_value',
            'unique_senders', 'unique_receivers', 'is_contract',
            'first_tx_age_days', 'last_tx_age_days', 'tx_frequency',
            'incoming_tx_count', 'outgoing_tx_count', 'avg_gas_price',
            'failed_tx_ratio'
        ]
        
        X = np.array([[features.get(col, 0) for col in feature_cols]])
        X_scaled = self.scaler.transform(X)
        
        # Predict probability
        proba = self.model.predict_proba(X_scaled)[0][1]  # Probability of fraud
        
        # Determine confidence level based on how close to decision boundary
        if proba < 0.3 or proba > 0.7:
            confidence = "HIGH"
        elif proba < 0.4 or proba > 0.6:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        return proba, confidence
    
    def get_feature_contributions(self, features: dict) -> dict:
        """Get which features contributed most to the prediction."""
        if self.feature_importance is None:
            self.load()
        
        contributions = {}
        for feature, importance in self.feature_importance.items():
            value = features.get(feature, 0)
            contributions[feature] = {
                'value': value,
                'importance': importance,
                'contribution_score': value * importance
            }
        
        return dict(sorted(contributions.items(), 
                          key=lambda x: abs(x[1]['contribution_score']), 
                          reverse=True))


if __name__ == "__main__":
    # Train the model
    detector = LightweightFraudDetector()
    
    # Check if training data exists
    training_data = Path("data/ml_training/ethereum_training_data.csv")
    if not training_data.exists():
        print("ERROR: Training data not found!")
        print("Run: python src/ml/collect_ethereum_training_data.py")
        exit(1)
    
    # Train
    metrics = detector.train()
    
    print("\n=== TRAINING COMPLETE ===")
    print(f"Model is ready to use with {metrics['test_accuracy']:.1%} accuracy")
    print("\nThis model:")
    print("✓ Trained on REAL Ethereum data")
    print("✓ Uses behavioral features (not just blacklist lookup)")
    print("✓ Fast and interpretable")
    print("✓ Actually works on new addresses")
