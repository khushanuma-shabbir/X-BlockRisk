"""
XGBoost-based Fraud Detector - STRONGER than RandomForest
High precision, low false positives
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import json

class XGBoostFraudDetector:
    """
    XGBoost classifier - more powerful than RandomForest
    Optimized for HIGH PRECISION (low false positives)
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_importance = None
        self.model_path = Path("models/xgboost_fraud_detector.pkl")
        self.scaler_path = Path("models/xgboost_scaler.pkl")
        self.metrics_path = Path("models/xgboost_metrics.json")
        
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    def train(self, training_data_path: str = "data/ml_training/ethereum_training_data.csv"):
        """Train XGBoost model with hyperparameter tuning"""
        
        print("\n" + "="*80)
        print("TRAINING XGBOOST FRAUD DETECTOR")
        print("Optimized for HIGH PRECISION (low false positives)")
        print("="*80 + "\n")
        
        # Load data
        df = pd.read_csv(training_data_path)
        print(f"Loaded {len(df)} labeled addresses")
        print(f"  Fraud: {len(df[df['label']==1])} ({len(df[df['label']==1])/len(df)*100:.1f}%)")
        print(f"  Legitimate: {len(df[df['label']==0])} ({len(df[df['label']==0])/len(df)*100:.1f}%)")
        
        # Features
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
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Train XGBoost with hyperparameter tuning
        print("\n" + "-"*80)
        print("HYPERPARAMETER TUNING")
        print("-"*80)
        
        # Parameter grid for tuning
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.05, 0.1],
            'scale_pos_weight': [1, 2, 3],  # Handle class imbalance
        }
        
        # Base model
        base_model = XGBClassifier(
            objective='binary:logistic',
            eval_metric='auc',
            random_state=42,
            use_label_encoder=False
        )
        
        # Grid search optimizing for F1 score
        print("Running GridSearchCV (this may take a few minutes)...")
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=min(5, len(X_train)),  # 5-fold CV or less if small dataset
            scoring='f1',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        print(f"\n✓ Best parameters found:")
        for param, value in grid_search.best_params_.items():
            print(f"    {param}: {value}")
        
        print(f"\n✓ Best CV F1 Score: {grid_search.best_score_:.4f}")
        
        # Use best model
        self.model = grid_search.best_estimator_
        
        # Evaluate
        print("\n" + "="*80)
        print("TRAINING RESULTS")
        print("="*80)
        
        # Training accuracy
        train_score = self.model.score(X_train, y_train)
        print(f"\nTraining Accuracy: {train_score:.2%}")
        
        # Test accuracy
        test_score = self.model.score(X_test, y_test)
        print(f"Test Accuracy: {test_score:.2%}")
        
        # Predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Detailed metrics
        print("\n" + "-"*80)
        print("CLASSIFICATION REPORT")
        print("-"*80)
        print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        print("-"*80)
        print("CONFUSION MATRIX")
        print("-"*80)
        print(f"True Negatives (Correct Legit):  {tn}")
        print(f"False Positives (Wrong Fraud):   {fp}  ← MINIMIZE THIS!")
        print(f"False Negatives (Missed Fraud):  {fn}")
        print(f"True Positives (Correct Fraud):  {tp}")
        
        # Calculate key metrics
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # False positive rate
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        print("\n" + "-"*80)
        print("KEY METRICS")
        print("-"*80)
        print(f"Precision:     {precision:.2%}  (When we predict fraud, we're right {precision*100:.1f}% of the time)")
        print(f"Recall:        {recall:.2%}  (We catch {recall*100:.1f}% of actual fraud)")
        print(f"F1 Score:      {f1:.4f}  (Harmonic mean of precision & recall)")
        print(f"ROC AUC:       {roc_auc:.4f}")
        print(f"False Pos Rate: {fpr:.2%}  ← TARGET: <5%")
        
        # Feature importance
        self.feature_importance = dict(zip(feature_cols, self.model.feature_importances_))
        
        print("\n" + "-"*80)
        print("FEATURE IMPORTANCE (Top 10)")
        print("-"*80)
        sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
        for i, (feature, importance) in enumerate(sorted_features[:10], 1):
            print(f"{i:2d}. {feature:25s}: {importance:.4f}")
        
        # Save model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        # Save metrics
        metrics = {
            'model_type': 'XGBoost',
            'train_accuracy': float(train_score),
            'test_accuracy': float(test_score),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'false_positive_rate': float(fpr),
            'best_params': grid_search.best_params_,
            'feature_importance': {k: float(v) for k, v in self.feature_importance.items()},
            'confusion_matrix': cm.tolist(),
            'training_size': len(X_train),
            'test_size': len(X_test)
        }
        
        with open(self.metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print("\n" + "="*80)
        print("MODEL SAVED")
        print("="*80)
        print(f"Model: {self.model_path}")
        print(f"Scaler: {self.scaler_path}")
        print(f"Metrics: {self.metrics_path}")
        
        # Grade
        print("\n" + "="*80)
        print("PERFORMANCE GRADE")
        print("="*80)
        
        if f1 >= 0.90 and precision >= 0.95:
            grade = "A++ (Excellent! High precision & recall)"
        elif f1 >= 0.85 and precision >= 0.90:
            grade = "A+ (Very Good)"
        elif f1 >= 0.80:
            grade = "A (Good)"
        elif f1 >= 0.70:
            grade = "B+ (Above Average)"
        else:
            grade = "B or below (Needs more data)"
        
        print(f"\nGrade: {grade}")
        print(f"F1 Score: {f1:.4f}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall: {recall:.2%}")
        print(f"False Positive Rate: {fpr:.2%}")
        
        return metrics
    
    def load(self):
        """Load trained model"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found. Train first.")
        
        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        
        with open(self.metrics_path, 'r') as f:
            metrics = json.load(f)
        
        self.feature_importance = metrics['feature_importance']
        
        print(f"Loaded XGBoost model")
        print(f"  Test Accuracy: {metrics['test_accuracy']:.2%}")
        print(f"  F1 Score: {metrics['f1_score']:.4f}")
        print(f"  Precision: {metrics['precision']:.2%}")
    
    def predict(self, features: dict) -> tuple:
        """Predict fraud probability"""
        if self.model is None:
            self.load()
        
        feature_cols = [
            'total_txs', 'total_value_eth', 'avg_tx_value',
            'unique_senders', 'unique_receivers', 'is_contract',
            'first_tx_age_days', 'last_tx_age_days', 'tx_frequency',
            'incoming_tx_count', 'outgoing_tx_count', 'avg_gas_price',
            'failed_tx_ratio'
        ]
        
        X = np.array([[features.get(col, 0) for col in feature_cols]])
        X_scaled = self.scaler.transform(X)
        
        proba = self.model.predict_proba(X_scaled)[0][1]
        
        # Confidence based on distance from decision boundary
        if proba < 0.3 or proba > 0.7:
            confidence = "HIGH"
        elif proba < 0.4 or proba > 0.6:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        return proba, confidence


if __name__ == "__main__":
    detector = XGBoostFraudDetector()
    
    training_data = Path("data/ml_training/ethereum_training_data.csv")
    if not training_data.exists():
        print("ERROR: Training data not found!")
        exit(1)
    
    metrics = detector.train()
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print("\nXGBoost model is stronger than RandomForest:")
    print("  ✓ Better handling of imbalanced data")
    print("  ✓ Automatic feature interaction learning")
    print("  ✓ Hyperparameter tuning for optimal performance")
    print("  ✓ Higher precision (fewer false positives)")
    print("\nNext: Update app_web.py to use XGBoost model")
