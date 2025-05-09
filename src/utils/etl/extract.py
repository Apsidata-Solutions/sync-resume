"""
Data loading utilities.

This module contains functions for loading and validating data from various sources.
"""

import logging
from typing import Optional, Dict, Any, List, Union, Tuple

import pandas as pd


# Configure logger
logger = logging.getLogger(__name__)

def load_excel_data(file_path: str, sheet_name: str = "Sheet1") -> Optional[pd.DataFrame]:
    """
    Load data from an Excel file.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to load (default: "Sheet1")
        
    Returns:
        DataFrame with the loaded data or None if an error occurs
    """
    try:
        logger.info(f"Loading data from {file_path}, sheet: {sheet_name}...")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        if df.empty:
            logger.warning(f"Loaded Excel file is empty: {file_path}")
            return None
            
        logger.info(f"Data loaded successfully. Total rows: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {e}", exc_info=True)
        return None

def validate_data(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate the loaded data for required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of column names that must be present
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    try:
        if df is None or df.empty:
            logger.error("Cannot validate empty or None DataFrame")
            return False, []
            
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False, missing_columns
            
        logger.info("All required columns present in the data")
        return True, []
    except Exception as e:
        logger.error(f"Error validating data: {e}", exc_info=True)
        return False, []

def take_sample(df: pd.DataFrame, sample_size: int = 100, random_state: int = None) -> pd.DataFrame:
    """
    Take a random sample from the DataFrame.
    
    Args:
        df: Source DataFrame
        sample_size: Number of rows to sample
        random_state: Random seed for reproducibility
        
    Returns:
        DataFrame with sampled rows
    """
    try:
        if df is None or df.empty:
            logger.error("Cannot sample from empty or None DataFrame")
            return pd.DataFrame()
            
        actual_sample_size = min(sample_size, len(df))
        sample = df.sample(actual_sample_size, random_state=random_state)
        
        logger.info(f"Sampled {len(sample)} rows from {len(df)} total rows")
        return sample
    except Exception as e:
        logger.error(f"Error sampling data: {e}", exc_info=True)
        return pd.DataFrame() 

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names in the dataframe.
    
    Args:
        df: DataFrame with original column names
        
    Returns:
        DataFrame with standardized column names
    """
    try:
        if df is None or df.empty:
            logger.warning("Cannot standardize column names for empty dataframe")
            return df
            
        # Define standard column mapping
        column_mapping = {
            "Id": "id",
            "FirstName": "first_name", 
            "LastName": "last_name", 
            "MobileNo": "old_mobile", 
            "WhatsAppNo": "old_whatsapp",
            "Email": "old_email", 
            "DOB": "date_of_birth",
            "CountryId": "country_id",
            "Country": "country",
            "StateId": "state_id",
            "State": "state",
            "City": "old_city",
            "Address": "address",
            "Pin": "pin_code",
            "Primary Skill": "old_skills",
            "Skill": "primary_skill",
            "Role": "old_role", 
            "Level": "old_level", 
            "Resume": "resume",
        }
        
        # Apply column renaming (only for columns that exist)
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        result_df = df.copy()
        result_df.rename(columns=existing_columns, inplace=True)
        
        logger.debug(f"Standardized {len(existing_columns)} column names")
        return result_df
    except Exception as e:
        logger.error(f"Error standardizing column names: {e}", exc_info=True)
        return df

def add_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add missing standard columns with default values.
    
    Args:
        df: DataFrame to augment with missing columns
        
    Returns:
        DataFrame with all required columns
    """
    try:
        if df is None or df.empty:
            logger.warning("Cannot add columns to empty dataframe")
            return df
            
        result_df = df.copy()
        
        # Define default columns and their values
        default_columns = {
            "prefix": None,
            "gender": None,
            "alternative_mobile": None,
            "alternative_email": None,
            "industry": "Education",
            "secondary_skill": None,
            "tertiary_skill": None,
            "career_start_date": None,
            "education": None,
            "experiences": None
        }
        
        # Add missing columns
        for col, default_val in default_columns.items():
            if col not in result_df.columns:
                result_df[col] = default_val
        
        added_columns = [col for col in default_columns if col not in df.columns]
        if added_columns:
            logger.debug(f"Added {len(added_columns)} missing columns")
            
        return result_df
    except Exception as e:
        logger.error(f"Error adding missing columns: {e}", exc_info=True)
        return df 

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the dataframe by standardizing column names and contact information.
    This is the Extract and part of the Transform phase of ETL.
    
    Args:
        df: Raw DataFrame to prepare
        normalizer: DataNormalizer instance
        
    Returns:
        Prepared DataFrame ready for processing
    """
    try:
        if df is None or df.empty:
            logger.warning("Cannot prepare empty DataFrame")
            return pd.DataFrame()
        
        # Step 1: Standardize column names
        df_standardized = standardize_column_names(df)
        logger.info("Column names standardized")
        
        # Step 2: Add missing standard columns
        df_with_columns = add_missing_columns(df_standardized)
        logger.info("Missing columns added")
        
        # # Step 3: Sanitize contact information
        # df_sanitized = normalizer.sanitize_contact_info(df_with_columns)
        # logger.info("Contact information sanitized")
        
        return df_with_columns
    except Exception as e:
        logger.error(f"Error preparing dataframe: {e}", exc_info=True)
        return df
