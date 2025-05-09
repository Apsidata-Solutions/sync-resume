"""
Main entry point for data preprocessing pipeline.

This module provides the high-level functions for orchestrating the entire
data preprocessing pipeline, including loading, processing, and saving data.
"""

import time
import logging
import argparse
from typing import Optional, Dict, Tuple, Any, Union

import pandas as pd

from src.utils.normalizer import DataNormalizer
from src.utils.extract import load_excel_data, validate_data, take_sample, prepare_dataframe
from src.utils.transform import process_dataframe, generate_matching_report
from src.utils.load import save_to_excel, save_report

# Configure logger
# logger = configure_logger(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Clear existing handlers to avoid duplicate logs
if logger.handlers:
    logger.handlers.clear()

# Create handler and set level
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

def test_sample(file_path: str, sample_size: int = 100, strategy: str = 'progressive') -> Optional[pd.DataFrame]:
    """
    Test the preprocessing pipeline on a sample of data.
    
    Args:
        file_path: Path to the Excel file
        sample_size: Number of rows to sample
        strategy: Matching strategy to use
        
    Returns:
        Processed DataFrame sample or None if an error occurs
    """
    try:
        logger.info(f"Testing sample of {sample_size} rows from {file_path}...")
        
        # Load, validate and prepare data
        df = load_excel_data(file_path)
        if df is None:
            return None
        
        is_valid, missing_columns = validate_data(df, ['Primary Skill'])
        if not is_valid:
            logger.error(f"Data validation failed: {missing_columns}")
            return None
        
        prepared_df = prepare_dataframe(sample_df)

        # Take a sample
        sample_df = take_sample(prepared_df, sample_size)

        normalizer = DataNormalizer()

        # Process the sample
        result = process_dataframe(sample_df, normalizer, strategy=strategy)
        
        logger.info(f"Sample processing completed successfully")
        return result
    
    except Exception as e:
        logger.error(f"Error processing sample: {e}", exc_info=True)
        return None

def run_full_processing(
    file_path: str, 
    output_path: Optional[str] = None, 
    strategy: str = 'progressive', 
    num_workers: Optional[int] = None
) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
    """
    Run the full preprocessing pipeline on all data and generate a report.
    
    Args:
        file_path: Path to the Excel file
        output_path: Path to save the processed data (optional)
        strategy: Matching strategy to use
        num_workers: Number of parallel workers (None = auto)
        
    Returns:
        Tuple of (processed_dataframe, report)
    """
    try:
        logger.info(f"Running full processing on {file_path}...")
        
        # Load data (Extract phase)
        df = load_excel_data(file_path)
        if df is None:
            return None, None
            
        # Validate data
        is_valid, missing_columns = validate_data(df, ['Primary Skill'])
        if not is_valid:
            logger.error(f"Data validation failed: {missing_columns}")
            return None, None
        
        # Process all data (Transform phase)
        total_rows = len(df)
        logger.info(f"Processing all {total_rows} rows with strategy: {strategy}...")
        
        # First prepare the dataframe (column standardization and sanitization)
        prepared_df = prepare_dataframe(df)

        # Initialize normalizer
        normalizer = DataNormalizer()

        result = process_dataframe(
            prepared_df, 
            normalizer, 
            strategy=strategy, 
            num_workers=num_workers
        )
        
        # Generate report
        report = generate_matching_report(result)
        
        # Save results if output path is provided (Load phase)
        if output_path and result is not None:
            save_success = save_to_excel(result, output_path)
            if save_success:
                logger.info(f"Results saved to {output_path}")
            else:
                logger.warning(f"Failed to save results to {output_path}")
                
            # Save report if output path is provided
            report_path = output_path.replace('.xlsx', '_report.txt')
            save_report(report, report_path)
        
        return result, report
    
    except Exception as e:
        logger.error(f"Error in full processing: {e}", exc_info=True)
        return None, None

def compare_strategies(
    input_path: str, 
    sample_size: int = 100, 
    primary_skill_column: str = 'skill'
) -> Optional[pd.DataFrame]:
    """
    Compare different matching strategies on a sample dataset.
    
    Args:
        df: Source DataFrame
        sample_size: Number of rows to sample for comparison
        primary_skill_column: Column name containing primary skill information
        
    Returns:
        DataFrame with comparison results or None if an error occurs
    """
    try:
        
        df = load_excel_data(input_path)
        if df is None or df.empty:
            logger.error("Cannot compare strategies on empty DataFrame")
            return None
        
        # Take a sample from the DataFrame
        sample = df.sample(min(sample_size, len(df)))
        
        strategies = ['direct', 'regex', 'fuzzy', 'vector', 'progressive']
        results = {}
        times = {}
        
        # Initialize the normalizer
        normalizer = DataNormalizer()
        
        for strategy in strategies:
            try:
                logger.info(f"Testing strategy: {strategy}")
                start_time = time.time()
                result = process_dataframe(
                    sample, 
                    normalizer, 
                    strategy=strategy
                )
                end_time = time.time()
                
                times[strategy] = end_time - start_time
                
                # Calculate success rates
                unknown_skills = (result['Skill'] == 'Unknown').sum()
                unknown_roles = (result['Role'] == 'Unknown').sum()
                
                results[strategy] = {
                    'time': times[strategy],
                    'skill_match_rate': (1 - unknown_skills/len(sample)) * 100,
                    'role_match_rate': (1 - unknown_roles/len(sample)) * 100
                }
                
                logger.info(f"Strategy {strategy} completed: "
                           f"time={times[strategy]:.2f}s, "
                           f"skill_rate={results[strategy]['skill_match_rate']:.2f}%, "
                           f"role_rate={results[strategy]['role_match_rate']:.2f}%")
                
            except Exception as e:
                logger.error(f"Error testing strategy {strategy}: {e}", exc_info=True)
                results[strategy] = {
                    'time': None,
                    'skill_match_rate': None,
                    'role_match_rate': None
                }
        
        return pd.DataFrame(results).T
    except Exception as e:
        logger.error(f"Error comparing strategies: {e}", exc_info=True)
        return None

def process_candidate_skills(
    input_path: str, 
    mode: str = 'test', 
    sample_size: int = 100, 
    strategy: str = 'progressive', 
    output_path: Optional[str] = None, 
    num_workers: Optional[int] = None
) -> Union[pd.DataFrame, None, pd.DataFrame]:
    """
    Main function to orchestrate data preprocessing pipeline.
    
    Args:
        input_path: Path to the Excel file
        mode: 'test' for sample testing, 'full' for full processing, 'compare' to compare strategies
        sample_size: Number of rows to sample for testing
        strategy: Matching strategy to use
        output_path: Path to save output Excel file (only used in 'full' mode)
        num_workers: Number of parallel workers (None = auto)
    
    Returns:
        DataFrame with results, or comparison report if mode='compare'
    """
    try:
        if mode == 'test':
            return test_sample(input_path, sample_size, strategy)
        elif mode == 'full':
            result, report = run_full_processing(input_path, output_path, strategy, num_workers)
            if report:
                logger.info("\nMatching Report:")
                logger.info(f"Total records processed: {report['summary']['total_records']}")
                logger.info(f"Skills identification rate: {report['summary']['identification_rate_skills']:.2f}%")
                logger.info(f"Roles identification rate: {report['summary']['identification_rate_roles']:.2f}%")
            return result
        elif mode == 'compare':
            return compare_strategies(input_path, sample_size)
        else:
            logger.error(f"Unknown mode: {mode}. Use 'test', 'full', or 'compare'.")
            return None
    except Exception as e:
        logger.error(f"Error processing candidate skills: {e}", exc_info=True)
        return None

# Entry point for command-line execution
if __name__ == "__main__":
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Process candidate skills data')
        parser.add_argument('--input_path', type=str, required=True, help='Path to the input Excel file')
        parser.add_argument('--output_path', type=str, help='Path to the output Excel file')
        parser.add_argument('--mode', type=str, default='test', choices=['test', 'full', 'compare'], 
                           help='Mode to run the script')
        parser.add_argument('--sample_size', type=int, default=100, help='Sample size to run the script')
        parser.add_argument('--strategy', type=str, default='progressive', 
                           choices=['direct', 'regex', 'fuzzy', 'vector', 'progressive'],
                           help='Matching strategy to use')
        parser.add_argument('--num_workers', type=int, help='Number of parallel workers')
        
        # Parse arguments
        args = parser.parse_args()
        logger.info(f"Running with arguments: {vars(args)}")
        
        # Run processing
        result = process_candidate_skills(
            input_path=args.input_path,
            mode=args.mode,
            sample_size=args.sample_size,
            strategy=args.strategy,
            output_path=args.output_path,
            num_workers=args.num_workers
        )
        
        # Print report or results summary
        if args.mode == 'compare':
            logger.info("\nStrategy Comparison:")
            logger.info(result)
        elif result is not None:
            logger.info(f"\nProcessing completed successfully. Results shape: {result.shape}")
            result.head()
        else:
            logger.error("Processing failed. Check logs for details.")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True) 
