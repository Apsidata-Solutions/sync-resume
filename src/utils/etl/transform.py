"""
Data processing utilities.

This module contains functions for processing and transforming data, including
parallel processing of data and standardizing column names and values.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from functools import partial
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from .normalizer import DataNormalizer, is_valid_mobile, is_valid_email

# Configure logger
logger = logging.getLogger(__name__)


def process_dataframe(df: pd.DataFrame, 
                     normalizer: DataNormalizer, 
                     primary_skill_column: str = 'old_skills',
                     strategy: str = 'progressive', 
                     num_workers: int = 4) -> Optional[pd.DataFrame]:
    """
    Process entire dataframe with parallel execution.
    This is the main Transform phase of ETL.
    
    Args:
        df: DataFrame to process
        normalizer: DataNormalizer instance
        primary_skill_column: Column name containing primary skill information
        strategy: Matching strategy to use
        num_workers: Number of parallel workers
        
    Returns:
        Processed DataFrame or None if an error occurs
    """
    try:
        if df is None or df.empty:
            logger.warning("Cannot process empty DataFrame")
            return None  
        start_time = time.time()
        
        results = []
        
        # Use ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # Submit all rows for processing
            futures = [executor.submit(normalizer.normalize_row, row, strategy) for _, row in df.iterrows()]
            
            # Collect results as they complete
            for future in futures:
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Error processing row in parallel execution: {e}", exc_info=True)
                    results.append({
                        "skill": None, 
                        "role": None, 
                        "level": None, 
                        "city": None, 
                        "mobile": None,
                        "whatsapp": None, 
                        "email": None
                    })
        
        # Convert results to DataFrame
        result_df = pd.DataFrame(results)
        
        # Add results back to original dataframe
        df_result = pd.concat([df.reset_index(drop=True), result_df], axis=1)
        
        end_time = time.time()
        logger.info(f"Processing completed in {end_time - start_time:.2f} seconds")
        logger.debug(f"Resulting dataframe columns: {df_result.columns}")
        # Apply status labeling
        return apply_status_labels(df_result)
    except Exception as e:
        logger.error(f"Error processing dataframe: {e}", exc_info=True)
        return None


def generate_matching_report(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Generate a report on the matching results.
    
    Args:
        df: Processed DataFrame
        
    Returns:
        Dictionary with report data or None if an error occurs
    """
    try:
        if df is None or df.empty:
            logger.error("No results to generate report from")
            return None
            
        total_rows = len(df)
            
        # Count known vs unknown
        unknown_skills = (df['skill'] == 'Unknown').sum()
        unknown_roles = (df['role'] == 'Unknown').sum()
        
        # Get distribution of roles, levels, and skills
        role_counts = df['role'].value_counts()
        level_counts = df['level'].value_counts()
        skill_counts = df['skill'].value_counts()
        
        report = {
            'summary': {
                'total_records': total_rows,
                'identified_skills': total_rows - unknown_skills,
                'identified_roles': total_rows - unknown_roles,
                'identification_rate_skills': (1 - unknown_skills/total_rows) * 100,
                'identification_rate_roles': (1 - unknown_roles/total_rows) * 100
            },
            'top_roles': role_counts.head(10).to_dict(),
            'top_levels': level_counts.head(5).to_dict(),
            'top_skills': skill_counts.head(10).to_dict(),
        }
        
        logger.info(f"Report generated: {total_rows} records processed")
        return report
    except Exception as e:
        logger.error(f"Error generating matching report: {e}", exc_info=True)
        return None


def apply_status_labels(df: pd.DataFrame, invert: bool = False) -> pd.DataFrame:
    """
    Apply status labels based on data quality.
    This is the final part of the Transform phase of ETL.
    
    Args:
        df: DataFrame to label
        invert: Whether to return rows that pass validation (True) or fail (False)
        
    Returns:
        Labeled DataFrame
    """
    try:
        if df is None or df.empty:
            logger.warning("Cannot apply status labels to empty DataFrame")
            return pd.DataFrame()
        
        result_df = df.copy()
        
        logger.debug(result_df.columns)
        # Apply validation filters
        if 'skill' in result_df.columns and 'mobile' in result_df.columns and 'email' in result_df.columns:
            skill_filter = result_df['skill'] != None
            number_filter = result_df["mobile"].apply(is_valid_mobile)
            email_filter = result_df["email"].apply(is_valid_email)
            city_filter = result_df["city"] != None

            logger.debug(f"City Filter: {city_filter.shape}, {city_filter.head()}")
            logger.debug(f"Number Filter: {number_filter.shape}, {number_filter.head()}")
            logger.debug(f"Email Filter: {email_filter.shape}, {email_filter.head()}")
            logger.debug(f"Skill Filter: {skill_filter.shape}, {skill_filter.head()}")

            filter_mask = skill_filter & number_filter & email_filter & city_filter
            
            # Set status (0 for pending, 3 for not needed)
            result_df["status"] = 0  # Default status is pending
            result_df.loc[filter_mask, "status"] = 3  # Status 3 for records that pass all filters
            
            logger.info(f"Status applied: {filter_mask.sum()} records passed all filters")
            
        return result_df
    except Exception as e:
        logger.error(f"Error applying status labels: {e}", exc_info=True)
        return df

