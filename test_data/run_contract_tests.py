"""
Smart Contract Test Runner
Tests the rule-based contract analysis module
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import contract analysis
from src.contract_analysis import analyze_contract

print("="*80)
print("SMART CONTRACT ANALYSIS - TEST SUITE")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Load test cases
test_file = 'test_data/CONTRACT_TEST_CASES.csv'
print(f"Loading test cases from: {test_file}")

try:
    df_tests = pd.read_csv(test_file)
    print(f"[OK] Loaded {len(df_tests)} test cases\n")
except Exception as e:
    print(f"[ERROR] Loading test file: {e}")
    sys.exit(1)

print(f"Test distribution:")
print(f"  LOW risk expected: {len(df_tests[df_tests['expected_risk'] == 'LOW'])}")
print(f"  MEDIUM risk expected: {len(df_tests[df_tests['expected_risk'] == 'MEDIUM'])}")
print(f"  HIGH risk expected: {len(df_tests[df_tests['expected_risk'] == 'HIGH'])}")
print(f"  CRITICAL risk expected: {len(df_tests[df_tests['expected_risk'] == 'CRITICAL'])}")

# Results storage
results = []

print(f"\n{'='*80}")
print("RUNNING TESTS")
print(f"{'='*80}\n")

# Run each test
for idx, row in df_tests.iterrows():
    test_id = row['test_id']
    contract_address = row['contract_address']
    expected_risk = row['expected_risk']
    expected_label = row['expected_label']
    description = row['description']
    notes = row['notes']
    
    print(f"[{idx+1}/{len(df_tests)}] {test_id}: {description}")
    print(f"  Contract: {contract_address}")
    print(f"  Expected: {expected_risk} RISK")
    
    try:
        # Analyze contract
        result = analyze_contract(contract_address)
        
        risk_score = result['risk_score']
        risk_category = result['risk_category']
        data_source = result['data_source']
        
        # Map score to category
        if risk_score < 30:
            actual_risk = 'LOW'
        elif risk_score < 50:
            actual_risk = 'MEDIUM'
        elif risk_score < 70:
            actual_risk = 'HIGH'
        else:
            actual_risk = 'CRITICAL'
        
        # Check if passed
        if actual_risk == expected_risk:
            status = 'PASS'
            print(f"  Result: [OK] {actual_risk} RISK (score: {risk_score})")
        elif (expected_risk == 'HIGH' and actual_risk == 'MEDIUM') or \
             (expected_risk == 'MEDIUM' and actual_risk == 'LOW') or \
             (expected_risk == 'CRITICAL' and actual_risk == 'HIGH'):
            status = 'PARTIAL'
            print(f"  Result: [PARTIAL] {actual_risk} RISK (expected {expected_risk}, score: {risk_score})")
        else:
            status = 'FAIL'
            print(f"  Result: [FAIL] {actual_risk} RISK (expected {expected_risk}, score: {risk_score})")
        
        # Store result
        results.append({
            'test_id': test_id,
            'contract_address': contract_address,
            'expected_risk': expected_risk,
            'actual_risk': actual_risk,
            'risk_score': risk_score,
            'risk_category': risk_category,
            'data_source': data_source,
            'status': status,
            'description': description
        })
        
    except Exception as e:
        print(f"  Result: [ERROR] {str(e)}")
        results.append({
            'test_id': test_id,
            'contract_address': contract_address,
            'expected_risk': expected_risk,
            'actual_risk': 'ERROR',
            'risk_score': -1,
            'risk_category': 'ERROR',
            'data_source': 'ERROR',
            'status': 'ERROR',
            'description': description
        })
    
    print()

# Save results
df_results = pd.DataFrame(results)
output_file = 'test_data/CONTRACT_TEST_RESULTS.csv'
df_results.to_csv(output_file, index=False)
print(f"[OK] Results saved to: {output_file}\n")

# Generate summary
total_tests = len(df_results)
passed = len(df_results[df_results['status'] == 'PASS'])
partial = len(df_results[df_results['status'] == 'PARTIAL'])
failed = len(df_results[df_results['status'] == 'FAIL'])
errors = len(df_results[df_results['status'] == 'ERROR'])

pass_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
adjusted_pass_rate = ((passed + partial * 0.5) / total_tests) * 100 if total_tests > 0 else 0

print("="*80)
print("TEST SUMMARY")
print("="*80)

print(f"\nTotal Tests: {total_tests}")
print(f"  [PASS] {passed} ({passed/total_tests*100:.1f}%)")
print(f"  [PARTIAL] {partial} ({partial/total_tests*100:.1f}%)")
print(f"  [FAIL] {failed} ({failed/total_tests*100:.1f}%)")
print(f"  [ERROR] {errors} ({errors/total_tests*100:.1f}%)")

print(f"\nPass Rate: {pass_rate:.1f}%")
print(f"Adjusted Pass Rate (partial = 0.5): {adjusted_pass_rate:.1f}%")

print(f"\n{'='*80}")
if pass_rate >= 70:
    print("[OK] GOOD - Contract analyzer working well")
elif pass_rate >= 50:
    print("[WARNING] ACCEPTABLE - Some improvements needed")
else:
    print("[ERROR] NEEDS WORK - Significant issues detected")
print(f"{'='*80}\n")

# Breakdown by risk level
print("\nBreakdown by Expected Risk Level:")
for risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
    subset = df_results[df_results['expected_risk'] == risk_level]
    if len(subset) > 0:
        subset_pass = len(subset[subset['status'] == 'PASS'])
        subset_rate = (subset_pass / len(subset)) * 100
        print(f"  {risk_level}: {subset_pass}/{len(subset)} passed ({subset_rate:.0f}%)")

print("\n" + "="*80)
print(f"Test run completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
