"""
Test Synthetic Patterns Only - No API Calls
Fast validation of synthetic test case coverage
"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_data.synthetic_generator import SyntheticFeatureGenerator
from src.detection.hybrid_detector import HybridDetector

def main():
    print("="*80)
    print("TESTING SYNTHETIC PATTERNS - NO API CALLS")
    print("="*80)
    
    # Load test cases
    df = pd.read_csv('test_data/MASTER_TEST_CASES.csv')
    
    # Filter to Ethereum synthetic patterns only
    synthetic = df[(df['chain'] == 'Ethereum') & (df['input_type'] == 'synthetic_features')]
    
    print(f"\nSynthetic Ethereum Patterns: {len(synthetic)}")
    print(f"  - Expected Fraud: {len(synthetic[synthetic['expected_label'] == 'Fraud'])}")
    print(f"  - Expected Legitimate: {len(synthetic[synthetic['expected_label'] == 'Legitimate'])}")
    
    # Initialize
    generator = SyntheticFeatureGenerator()
    detector = HybridDetector()
    
    # Test results
    results = []
    
    print("\n" + "="*80)
    print("RUNNING TESTS")
    print("="*80)
    
    for idx, row in synthetic.iterrows():
        test_id = row['test_id']
        pattern_name = row['input']
        expected_label = row['expected_label']
        expected_range = row['expected_risk_range']
        
        # Parse range
        if '-' in expected_range:
            min_risk, max_risk = map(int, expected_range.split('-'))
        else:
            min_risk = max_risk = int(expected_range)
        
        # Generate features
        features = generator.generate(pattern_name)
        
        if not features or sum(features.values()) == 0:
            print(f"XX [{test_id}] Pattern '{pattern_name}' not found")
            results.append({
                'test_id': test_id,
                'pattern': pattern_name,
                'status': 'ERROR',
                'reason': 'Pattern not found'
            })
            continue
        
        # Run detection
        score, category, _ = detector.detect(f'synthetic_{test_id}', features, gnn_score=0)
        
        # Check range
        in_range = min_risk <= score <= max_risk
        
        if in_range:
            status = 'PASS'
            symbol = 'OK'
        else:
            status = 'FAIL'
            symbol = 'XX'
        
        print(f"{symbol} [{test_id}] {pattern_name[:40]:<40} | Score: {score:>5.1f} | Expected: [{min_risk:>3}-{max_risk:<3}] | {expected_label}")
        
        results.append({
            'test_id': test_id,
            'pattern': pattern_name,
            'expected_label': expected_label,
            'expected_range': expected_range,
            'score': score,
            'category': category,
            'status': 'PASS' if in_range else 'FAIL',
            'in_range': in_range
        })
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    results_df = pd.DataFrame(results)
    
    total = len(results_df)
    passed = len(results_df[results_df['status'] == 'PASS'])
    failed = len(results_df[results_df['status'] == 'FAIL'])
    errors = len(results_df[results_df['status'] == 'ERROR'])
    
    print(f"\nTotal Tests: {total}")
    print(f"  Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"  Errors: {errors}")
    
    # By expected label
    print("\nBy Expected Label:")
    for label in ['Fraud', 'Legitimate']:
        subset = results_df[results_df['expected_label'] == label]
        if len(subset) > 0:
            subset_passed = len(subset[subset['status'] == 'PASS'])
            subset_total = len(subset)
            print(f"  {label}: {subset_passed}/{subset_total} ({subset_passed/subset_total*100:.1f}%)")
    
    # Failed cases
    if failed > 0:
        print("\nFailed Cases:")
        failed_cases = results_df[results_df['status'] == 'FAIL']
        for idx, row in failed_cases.iterrows():
            print(f"  - [{row['test_id']}] {row['pattern'][:50]}")
            print(f"      Score: {row['score']:.1f} | Expected: {row['expected_range']} | Label: {row['expected_label']}")
    
    # Grade
    print("\n" + "="*80)
    pass_rate = passed / total * 100 if total > 0 else 0
    
    if pass_rate >= 85:
        grade = "A+"
    elif pass_rate >= 80:
        grade = "A"
    elif pass_rate >= 75:
        grade = "B+"
    elif pass_rate >= 70:
        grade = "B"
    else:
        grade = "C or below"
    
    print(f"Synthetic Pattern Coverage: {pass_rate:.1f}%")
    print(f"Estimated Grade Contribution: {grade}")
    print("="*80)

if __name__ == '__main__':
    main()
