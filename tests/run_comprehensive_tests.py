"""
Comprehensive Test Runner - All Ethereum Cases
Runs all real addresses + all synthetic patterns
"""
import sys
import os
import pandas as pd
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_data.run_all_tests import TestRunner

def main():
    print("="*80)
    print("COMPREHENSIVE TEST SUITE - ALL ETHEREUM CASES")
    print("="*80)
    
    # Load test cases
    df = pd.read_csv('test_data/MASTER_TEST_CASES.csv')
    
    # Filter to Ethereum only
    eth_cases = df[df['chain'] == 'Ethereum']
    
    print(f"\nTotal Test Cases: {len(df)}")
    print(f"Ethereum Cases: {len(eth_cases)}")
    print(f"  - Real Addresses: {len(eth_cases[eth_cases['input_type'] == 'real_address'])}")
    print(f"  - Synthetic Patterns: {len(eth_cases[eth_cases['input_type'] == 'synthetic_features'])}")
    print(f"Solana Cases (skipped): {len(df[df['chain'] == 'Solana'])}")
    
    # Initialize runner
    runner = TestRunner()
    
    # Test Strategy
    print("\n" + "="*80)
    print("TEST STRATEGY")
    print("="*80)
    print("1. Run ALL real Ethereum addresses (27 tests)")
    print("2. Run ALL synthetic Ethereum patterns (55 tests)")
    print("3. Skip Solana (not supported)")
    print("4. Generate comprehensive report")
    
    input("\nPress Enter to start tests (this will take ~10 minutes for API calls)...")
    
    # Run tests
    print("\n" + "="*80)
    print("RUNNING TESTS")
    print("="*80)
    
    start_time = datetime.now()
    
    # Run all tests (no limit, but will skip Solana automatically)
    results_df = runner.run_all_tests(limit=None)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Generate reports
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    runner.generate_report()
    
    # Additional statistics
    print("\n" + "="*80)
    print("DETAILED BREAKDOWN")
    print("="*80)
    
    # By status
    print("\nBy Status:")
    status_counts = results_df['status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # By input type
    print("\nBy Input Type:")
    for input_type in ['real_address', 'synthetic_features']:
        subset = results_df[results_df['input'].str.contains(input_type) | 
                           (results_df['test_id'].str.startswith('ETH_') & 
                            (results_df['actual_category'] != 'SKIPPED'))]
        if len(subset) > 0:
            passed = len(subset[subset['status'] == 'PASS'])
            total = len(subset)
            print(f"  {input_type}: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    # By expected label
    print("\nBy Expected Label:")
    for label in ['Fraud', 'Legitimate']:
        subset = results_df[results_df['expected_label'] == label]
        subset = subset[subset['status'] != 'SKIP']
        if len(subset) > 0:
            passed = len(subset[subset['status'] == 'PASS'])
            total = len(subset)
            print(f"  {label}: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    print(f"\nTotal Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"\nReports saved:")
    print(f"  - test_results/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    print(f"  - test_results/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    # Success criteria
    print("\n" + "="*80)
    print("PASS CRITERIA FOR A+ GRADE")
    print("="*80)
    
    total_applicable = len(results_df[results_df['status'] != 'SKIP'])
    total_passed = len(results_df[results_df['status'] == 'PASS'])
    pass_rate = total_passed / total_applicable * 100 if total_applicable > 0 else 0
    
    print(f"Overall Pass Rate: {pass_rate:.1f}%")
    print(f"  - Target: >= 80%")
    print(f"  - Status: {'✅ PASS' if pass_rate >= 80 else '❌ NEEDS IMPROVEMENT'}")
    
    # Fraud detection accuracy
    fraud_cases = results_df[results_df['expected_label'] == 'Fraud']
    fraud_cases = fraud_cases[fraud_cases['status'] != 'SKIP']
    fraud_passed = len(fraud_cases[fraud_cases['status'] == 'PASS'])
    fraud_total = len(fraud_cases)
    fraud_rate = fraud_passed / fraud_total * 100 if fraud_total > 0 else 0
    
    print(f"\nFraud Detection Rate: {fraud_rate:.1f}%")
    print(f"  - Target: >= 85%")
    print(f"  - Status: {'✅ PASS' if fraud_rate >= 85 else '❌ NEEDS IMPROVEMENT'}")
    
    # Legitimate false positive rate
    legit_cases = results_df[results_df['expected_label'] == 'Legitimate']
    legit_cases = legit_cases[legit_cases['status'] != 'SKIP']
    legit_passed = len(legit_cases[legit_cases['status'] == 'PASS'])
    legit_total = len(legit_cases)
    legit_rate = legit_passed / legit_total * 100 if legit_total > 0 else 0
    
    print(f"\nLegitimate Accuracy: {legit_rate:.1f}%")
    print(f"  - Target: >= 75%")
    print(f"  - Status: {'✅ PASS' if legit_rate >= 75 else '❌ NEEDS IMPROVEMENT'}")
    
    print("\n" + "="*80)
    
    if pass_rate >= 80 and fraud_rate >= 85 and legit_rate >= 75:
        print("✅ ALL CRITERIA MET - A+ GRADE ACHIEVABLE")
    else:
        print("⚠️  SOME CRITERIA NOT MET - REVIEW FAILED CASES")
    
    print("="*80)

if __name__ == '__main__':
    main()
