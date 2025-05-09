"""
Utilities package for data preprocessing and normalization.
"""

from src.utils.normalizer import DataNormalizer
from src.utils.extract import load_excel_data, validate_data, take_sample
from src.utils.transform import (
    process_dataframe, 
    prepare_dataframe,
    apply_status_labels,
    generate_matching_report,
)
from src.utils.load import save_to_excel, save_to_csv, save_report
from src.utils.etl import process_candidate_skills, compare_strategies

# Export key functions
__all__ = [
    # Main classes
    'DataNormalizer',
    
    # Core processing functions
    'process_dataframe',
    'prepare_dataframe',
    'apply_status_labels',
    'generate_matching_report',
    
    # Data loading functions
    'load_excel_data',
    'validate_data',
    'take_sample',
    
    # Data saving functions
    'save_to_excel',
    'save_to_csv',
    'save_report',
    
    # Main orchestration functions
    'process_candidate_skills',
    'compare_strategies',
]
