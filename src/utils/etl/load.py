"""
Data saving utilities.

This module contains functions for saving processed data to various output formats.
"""

import os
import logging
from typing import Optional, Dict, Any, Union

import pandas as pd

# Configure logger
logger = logging.getLogger(__name__)

def save_to_excel(df: pd.DataFrame, output_path: str, sheet_name: str = "Sheet1") -> bool:
    """
    Save a DataFrame to an Excel file.
    
    Args:
        df: DataFrame to save
        output_path: Path where the Excel file will be saved
        sheet_name: Name of the sheet (default: "Sheet1")
        
    Returns:
        True if saving was successful, False otherwise
    """
    try:
        if df is None or df.empty:
            logger.warning("Cannot save empty DataFrame to Excel")
            return False
            
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Save to Excel
        df.to_excel(output_path, sheet_name=sheet_name, index=False)
        
        logger.info(f"DataFrame successfully saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving DataFrame to Excel ({output_path}): {e}", exc_info=True)
        return False


def save_to_csv(df: pd.DataFrame, output_path: str, 
               delimiter: str = ",", encoding: str = "utf-8") -> bool:
    """
    Save a DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path where the CSV file will be saved
        delimiter: Field delimiter (default: ",")
        encoding: File encoding (default: "utf-8")
        
    Returns:
        True if saving was successful, False otherwise
    """
    try:
        if df is None or df.empty:
            logger.warning("Cannot save empty DataFrame to CSV")
            return False
            
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Save to CSV
        df.to_csv(output_path, sep=delimiter, encoding=encoding, index=False)
        
        logger.info(f"DataFrame successfully saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving DataFrame to CSV ({output_path}): {e}", exc_info=True)
        return False


def save_report(report: Dict[str, Any], output_path: str) -> bool:
    """
    Save a report dictionary to a text file.
    
    Args:
        report: Report dictionary
        output_path: Path where the report will be saved
        
    Returns:
        True if saving was successful, False otherwise
    """
    try:
        if not report:
            logger.warning("Cannot save empty report")
            return False
            
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_path, 'w') as f:
            # Write summary section
            f.write("===== MATCHING REPORT =====\n\n")
            
            summary = report.get('summary', {})
            f.write(f"Total records: {summary.get('total_records', 0)}\n")
            f.write(f"Identified skills: {summary.get('identified_skills', 0)}\n")
            f.write(f"Identified roles: {summary.get('identified_roles', 0)}\n")
            f.write(f"Skill identification rate: {summary.get('identification_rate_skills', 0):.2f}%\n")
            f.write(f"Role identification rate: {summary.get('identification_rate_roles', 0):.2f}%\n\n")
            
            # Write top roles
            f.write("==== TOP ROLES ====\n")
            for role, count in report.get('top_roles', {}).items():
                f.write(f"{role}: {count}\n")
            f.write("\n")
            
            # Write top levels
            f.write("==== TOP LEVELS ====\n")
            for level, count in report.get('top_levels', {}).items():
                f.write(f"{level}: {count}\n")
            f.write("\n")
            
            # Write top skills
            f.write("==== TOP SKILLS ====\n")
            for skill, count in report.get('top_skills', {}).items():
                f.write(f"{skill}: {count}\n")
                
        logger.info(f"Report successfully saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving report to {output_path}: {e}", exc_info=True)
        return False 