"""
Automated Test Runner - Tests All 100+ Cases from MASTER_TEST_CASES.csv
Generates comprehensive test report with pass/fail analysis
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add parent to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.detection.hybrid_detector import HybridDetector
from src.live.fetch_ethereum import fetch_ethereum_wallet
from test_data.synthetic_generator import SyntheticFeatureGenerator

class TestRunner:
    """Automated test runner for all test cases"""
    
    def __init__(self, test_csv='test_data/MASTER_TEST_CASES.csv'):
        self.test_cases = pd.read_csv(test_csv)
        self.generator = SyntheticFeatureGenerator()
        self.detector = HybridDetector()
        self.results = []
        
        print(f"Loaded {len(self.test_cases)} test cases")
    
    def parse_risk_range(self, risk_range_str):
        """Parse '70-100' to (70, 100)"""
        try:
            parts = risk_range_str.split('-')
            return int(parts[0]), int(parts[1])
        except:
            return 0, 100
    
    def run_single_test(self, test_case):
        """Run one test case"""
        test_id = test_case['test_id']
        chain = test_case['chain']
        input_val = test_case['input']
        input_type = test_case['input_type']
        expected_label = test_case['expected_label']
        expected_range = test_case['expected_risk_range']
        source = test_case.get('source', 'Unknown')
        
        print(f"\n[{test_id}] Testing {input_type}: {input_val[:40]}...")
        
        # Skip Solana for now (Phase 1 is Ethereum only)
        if chain == 'Solana':
            return {
                'test_id': test_id,
                'chain': chain,
                'input': input_val,
                'expected_label': expected_label,
                'expected_range': expected_range,
                'actual_score': 0,
                'actual_category': 'SKIPPED',
                'status': 'SKIP',
                'reason': 'Solana not supported in Phase 1',
                'source': source
            }
        
        try:
            # Get features based on input type
            if input_type == 'real_address':
                # Fetch live data
                try:
                    features, _, _, _ = fetch_ethereum_wallet(input_val)
                    if not features:
                        raise Exception("No features returned")
                except Exception as e:
                    return {
                        'test_id': test_id,
                        'chain': chain,
                        'input': input_val,
                        'expected_label': expected_label,
                        'expected_range': expected_range,
                        'actual_score': 0,
                        'actual_category': 'ERROR',
                        'status': 'FAIL',
                        'reason': f'API Error: {str(e)}',
                        'source': source
                    }
            
            elif input_type == 'synthetic_features':
                # Generate synthetic features
                features = self.generator.generate(input_val)
                if not features or sum(features.values()) == 0:
                    return {
                        'test_id': test_id,
                        'chain': chain,
                        'input': input_val,
                        'expected_label': expected_label,
                        'expected_range': expected_range,
                        'actual_score': 0,
                        'actual_category': 'ERROR',
                        'status': 'FAIL',
                        'reason': 'Synthetic pattern not found',
                        'source': source
                    }
            else:
                return {
                    'test_id': test_id,
                    'chain': chain,
                    'input': input_val,
                    'expected_label': expected_label,
                    'expected_range': expected_range,
                    'actual_score': 0,
                    'actual_category': 'ERROR',
                    'status': 'FAIL',
                    'reason': f'Unknown input type: {input_type}',
                    'source': source
                }
            
            # Run detection
            score, category, explanations = self.detector.detect(
                input_val if input_type == 'real_address' else f'synthetic_{test_id}',
                features,
                gnn_score=0  # GNN score is computed inside for real addresses
            )
            
            # Check if in expected range
            min_risk, max_risk = self.parse_risk_range(expected_range)
            in_range = min_risk <= score <= max_risk
            
            # Determine status
            if in_range:
                status = 'PASS'
                reason = f'Score {score:.0f} in range [{min_risk}-{max_risk}]'
            else:
                status = 'FAIL'
                reason = f'Score {score:.0f} outside range [{min_risk}-{max_risk}]'
            
            print(f"  → {status}: {score:.0f}/100 ({category}) - {reason}")
            
            return {
                'test_id': test_id,
                'chain': chain,
                'input': input_val,
                'expected_label': expected_label,
                'expected_range': expected_range,
                'actual_score': round(score, 1),
                'actual_category': category,
                'status': status,
                'reason': reason,
                'source': source,
                'explanations': ' | '.join(explanations[:3])  # First 3 explanations
            }
        
        except Exception as e:
            print(f"  → ERROR: {str(e)}")
            return {
                'test_id': test_id,
                'chain': chain,
                'input': input_val,
                'expected_label': expected_label,
                'expected_range': expected_range,
                'actual_score': 0,
                'actual_category': 'ERROR',
                'status': 'ERROR',
                'reason': str(e),
                'source': source
            }
    
    def run_all_tests(self, limit=None):
        """Run all test cases (or limited number)"""
        print("="*80)
        print("STARTING AUTOMATED TEST RUN")
        print("="*80)
        
        test_subset = self.test_cases.head(limit) if limit else self.test_cases
        
        for idx, row in test_subset.iterrows():
            result = self.run_single_test(row)
            self.results.append(result)
        
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        df = pd.DataFrame(self.results)
        
        # Summary statistics
        total = len(df)
        passed = len(df[df['status'] == 'PASS'])
        failed = len(df[df['status'] == 'FAIL'])
        skipped = len(df[df['status'] == 'SKIP'])
        errors = len(df[df['status'] == 'ERROR'])
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Total Tests:   {total}")
        print(f"✅ Passed:     {passed} ({pass_rate:.1f}%)")
        print(f"❌ Failed:     {failed}")
        print(f"⏭️  Skipped:    {skipped}")
        print(f"⚠️  Errors:     {errors}")
        print("="*80)
        
        # Breakdown by category
        if 'expected_label' in df.columns:
            print("\n📊 Breakdown by Expected Label:")
            for label in df['expected_label'].unique():
                label_df = df[df['expected_label'] == label]
                label_passed = len(label_df[label_df['status'] == 'PASS'])
                label_total = len(label_df)
                label_rate = (label_passed / label_total * 100) if label_total > 0 else 0
                print(f"  {label}: {label_passed}/{label_total} ({label_rate:.0f}%)")
        
        # Save detailed results
        output_file = 'test_data/test_results.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Generate HTML report
        self.generate_html_report(df)
        
        # Show failures
        failures = df[df['status'] == 'FAIL']
        if len(failures) > 0:
            print(f"\n❌ Failed Tests ({len(failures)}):")
            for idx, row in failures.head(10).iterrows():
                print(f"  [{row['test_id']}] {row['input'][:40]} - {row['reason']}")
            if len(failures) > 10:
                print(f"  ... and {len(failures) - 10} more (see CSV)")
    
    def generate_html_report(self, df):
        """Generate HTML test report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Results Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .stats {{ display: flex; gap: 20px; }}
        .stat {{ padding: 15px; border-radius: 5px; flex: 1; text-align: center; }}
        .passed {{ background: #d4edda; color: #155724; }}
        .failed {{ background: #f8d7da; color: #721c24; }}
        .skipped {{ background: #fff3cd; color: #856404; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .PASS {{ color: green; font-weight: bold; }}
        .FAIL {{ color: red; font-weight: bold; }}
        .SKIP {{ color: orange; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🧪 Blockchain Fraud Detection - Test Results</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat passed">
                <h3>{len(df[df['status'] == 'PASS'])}</h3>
                <p>Passed</p>
            </div>
            <div class="stat failed">
                <h3>{len(df[df['status'] == 'FAIL'])}</h3>
                <p>Failed</p>
            </div>
            <div class="stat skipped">
                <h3>{len(df[df['status'] == 'SKIP'])}</h3>
                <p>Skipped</p>
            </div>
        </div>
        <h3>Pass Rate: {(len(df[df['status'] == 'PASS']) / len(df) * 100):.1f}%</h3>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>Test ID</th>
            <th>Chain</th>
            <th>Input</th>
            <th>Expected</th>
            <th>Actual Score</th>
            <th>Status</th>
            <th>Reason</th>
        </tr>
"""
        
        for _, row in df.iterrows():
            input_display = row['input'][:50] + '...' if len(str(row['input'])) > 50 else row['input']
            html += f"""
        <tr>
            <td>{row['test_id']}</td>
            <td>{row['chain']}</td>
            <td>{input_display}</td>
            <td>{row['expected_range']}</td>
            <td>{row['actual_score']:.0f}</td>
            <td class="{row['status']}">{row['status']}</td>
            <td>{row['reason'][:80]}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        
        output_file = 'test_data/test_report.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📄 HTML report saved to: {output_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run automated tests')
    parser.add_argument('--limit', type=int, help='Limit number of tests (for quick testing)')
    parser.add_argument('--real-only', action='store_true', help='Run only real address tests')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Filter if needed
    if args.real_only:
        runner.test_cases = runner.test_cases[runner.test_cases['input_type'] == 'real_address']
        print(f"Filtered to {len(runner.test_cases)} real address tests")
    
    runner.run_all_tests(limit=args.limit)
