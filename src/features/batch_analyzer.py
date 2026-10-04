"""
Batch Analysis Module
Analyzes multiple wallet addresses in parallel and exports results to CSV.

Production Features:
- CSV upload/download support
- Parallel processing (100+ addresses)
- Progress tracking with ETA
- Export with risk scores and explanations
- Error handling per address (doesn't fail entire batch)
"""

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
from typing import List, Dict, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """
    Batch wallet analysis with parallel processing
    """
    
    def __init__(self, analysis_func, max_workers: int = 10):
        """
        Initialize batch analyzer
        
        Args:
            analysis_func: Function that takes (address) and returns (risk_score, reasons)
            max_workers: Number of parallel workers (default: 10)
        """
        self.analysis_func = analysis_func
        self.max_workers = max_workers
        self.results = []
        self.errors = []
    
    def analyze_single(self, address: str, index: int, total: int) -> Dict:
        """
        Analyze a single address with error handling
        
        Args:
            address: Wallet address to analyze
            index: Current index in batch
            total: Total number of addresses
        
        Returns:
            dict with analysis results or error info
        """
        try:
            start_time = time.time()
            
            # Run analysis
            risk_score, reasons = self.analysis_func(address)
            
            elapsed = time.time() - start_time
            
            logger.info(f"[{index}/{total}] ✓ {address[:10]}... | Risk: {risk_score}/100 | {elapsed:.1f}s")
            
            return {
                'address': address,
                'risk_score': risk_score,
                'risk_category': self._get_risk_category(risk_score),
                'reasons': '; '.join(reasons) if reasons else 'No patterns detected',
                'status': 'success',
                'analysis_time': round(elapsed, 2),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"[{index}/{total}] ✗ {address[:10]}... | Error: {str(e)}")
            
            return {
                'address': address,
                'risk_score': None,
                'risk_category': 'Error',
                'reasons': f'Analysis failed: {str(e)}',
                'status': 'error',
                'analysis_time': None,
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_batch(
        self, 
        addresses: List[str], 
        progress_callback: Optional[callable] = None
    ) -> pd.DataFrame:
        """
        Analyze multiple addresses in parallel
        
        Args:
            addresses: List of wallet addresses
            progress_callback: Optional callback function(completed, total, eta)
        
        Returns:
            pandas DataFrame with results
        """
        total = len(addresses)
        completed = 0
        start_time = time.time()
        
        logger.info(f"Starting batch analysis: {total} addresses with {self.max_workers} workers")
        
        results = []
        
        # Parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_address = {
                executor.submit(self.analyze_single, addr, idx+1, total): addr 
                for idx, addr in enumerate(addresses)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_address):
                result = future.result()
                results.append(result)
                completed += 1
                
                # Calculate ETA
                elapsed = time.time() - start_time
                avg_time_per_address = elapsed / completed
                remaining = total - completed
                eta_seconds = avg_time_per_address * remaining
                
                # Progress callback
                if progress_callback:
                    progress_callback(completed, total, eta_seconds)
                
                # Log progress
                if completed % 10 == 0 or completed == total:
                    logger.info(
                        f"Progress: {completed}/{total} "
                        f"({100*completed/total:.1f}%) | "
                        f"ETA: {eta_seconds/60:.1f}min"
                    )
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Calculate batch statistics
        success_count = (df['status'] == 'success').sum()
        error_count = (df['status'] == 'error').sum()
        avg_risk = df[df['status'] == 'success']['risk_score'].mean()
        
        total_time = time.time() - start_time
        
        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH ANALYSIS COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total addresses: {total}")
        logger.info(f"Successful: {success_count} ({100*success_count/total:.1f}%)")
        logger.info(f"Errors: {error_count} ({100*error_count/total:.1f}%)")
        logger.info(f"Average risk score: {avg_risk:.1f}/100")
        logger.info(f"Total time: {total_time/60:.1f} minutes")
        logger.info(f"Average time per address: {total_time/total:.1f} seconds")
        
        return df
    
    def analyze_from_csv(
        self, 
        input_path: str, 
        address_column: str = 'address',
        progress_callback: Optional[callable] = None
    ) -> pd.DataFrame:
        """
        Analyze addresses from CSV file
        
        Args:
            input_path: Path to input CSV file
            address_column: Name of column containing addresses
            progress_callback: Optional progress callback
        
        Returns:
            pandas DataFrame with results
        """
        logger.info(f"Loading addresses from: {input_path}")
        
        # Load CSV
        df_input = pd.read_csv(input_path)
        
        if address_column not in df_input.columns:
            raise ValueError(
                f"Column '{address_column}' not found. "
                f"Available columns: {list(df_input.columns)}"
            )
        
        # Extract addresses
        addresses = df_input[address_column].dropna().unique().tolist()
        
        logger.info(f"Found {len(addresses)} unique addresses")
        
        # Run batch analysis
        df_results = self.analyze_batch(addresses, progress_callback)
        
        return df_results
    
    def save_results(
        self, 
        df: pd.DataFrame, 
        output_path: str,
        include_summary: bool = True
    ):
        """
        Save results to CSV
        
        Args:
            df: Results DataFrame
            output_path: Output CSV path
            include_summary: Whether to include summary statistics
        """
        logger.info(f"Saving results to: {output_path}")
        
        # Sort by risk score (highest first)
        df_sorted = df.sort_values('risk_score', ascending=False, na_position='last')
        
        # Save main results
        df_sorted.to_csv(output_path, index=False)
        
        logger.info(f"✓ Saved {len(df)} results to {output_path}")
        
        # Save summary statistics if requested
        if include_summary:
            summary_path = output_path.replace('.csv', '_summary.txt')
            
            with open(summary_path, 'w') as f:
                f.write("BATCH ANALYSIS SUMMARY\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Total addresses analyzed: {len(df)}\n")
                f.write(f"Successful: {(df['status']=='success').sum()}\n")
                f.write(f"Errors: {(df['status']=='error').sum()}\n\n")
                
                # Risk distribution
                df_success = df[df['status'] == 'success']
                if len(df_success) > 0:
                    f.write("RISK DISTRIBUTION:\n")
                    f.write(f"  Average risk score: {df_success['risk_score'].mean():.1f}/100\n")
                    f.write(f"  Median risk score: {df_success['risk_score'].median():.1f}/100\n")
                    f.write(f"  Min risk score: {df_success['risk_score'].min():.1f}/100\n")
                    f.write(f"  Max risk score: {df_success['risk_score'].max():.1f}/100\n\n")
                    
                    # Category breakdown
                    f.write("RISK CATEGORIES:\n")
                    category_counts = df_success['risk_category'].value_counts()
                    for category, count in category_counts.items():
                        pct = 100 * count / len(df_success)
                        f.write(f"  {category}: {count} ({pct:.1f}%)\n")
                    f.write("\n")
                
                # Performance stats
                if df['analysis_time'].notna().any():
                    f.write("PERFORMANCE:\n")
                    f.write(f"  Average analysis time: {df['analysis_time'].mean():.1f}s\n")
                    f.write(f"  Total time: {df['analysis_time'].sum()/60:.1f} minutes\n")
                
            logger.info(f"✓ Saved summary to {summary_path}")
    
    @staticmethod
    def _get_risk_category(risk_score: float) -> str:
        """Convert risk score to category"""
        if risk_score is None or np.isnan(risk_score):
            return 'Unknown'
        elif risk_score < 33:
            return 'Low Risk'
        elif risk_score < 66:
            return 'Medium Risk'
        else:
            return 'High Risk'


def create_batch_template(output_path: str = 'batch_template.csv'):
    """
    Create a CSV template for batch analysis
    
    Args:
        output_path: Where to save template
    """
    template = pd.DataFrame({
        'address': [
            '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
            '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
            'Add more addresses here...'
        ],
        'label': ['example_1', 'example_2', 'optional_label'],
        'notes': ['Optional notes', '', 'Can be empty']
    })
    
    template.to_csv(output_path, index=False)
    logger.info(f"✓ Created batch template: {output_path}")
    logger.info(f"  Fill in the 'address' column and upload for batch analysis")


# Example usage
if __name__ == '__main__':
    # Create template
    create_batch_template()
    
    print("\nBatch Analysis Module Ready")
    print("="*60)
    print("Features:")
    print("  ✓ CSV upload/download")
    print("  ✓ Parallel processing (100+ addresses)")
    print("  ✓ Progress tracking with ETA")
    print("  ✓ Export with risk scores and explanations")
    print("  ✓ Per-address error handling")
    print("  ✓ Automatic summary statistics")
