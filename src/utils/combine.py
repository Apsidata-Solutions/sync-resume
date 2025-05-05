import pandas as pd
import os
import glob
import logging  

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    # Define colors for different log levels (green to red color scheme)
    COLORS = {
        'DEBUG': '\033[36m',   # Cyan
        'INFO': '\033[92m',    # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[31;1m', # Bright Red
        'RESET': '\033[0m'      # Reset to default
    }
    
    # Custom formatter with colors
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            levelname = record.levelname
            if levelname in COLORS:
                record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
            return super().format(record)
    
    formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

# Define the directory where processed CSV files are stored
processed_dir = "data/processed/"

# Get a list of all CSV files in the processed directory
csv_files = glob.glob(os.path.join(processed_dir, "*.csv"))

# Check if any files were found
if not csv_files:
    logger.warning("No CSV files found in the processed directory.")
    combined_df = pd.DataFrame()
else:
    logger.info(f"Found {len(csv_files)} CSV files to combine.")
    
    # Initialize an empty list to store individual dataframes
    dfs = []
    
    # Read each CSV file and append to the list
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            logger.info(f"Added {file} with {len(df)} rows")
        except Exception as e:
            logger.error(f"Error reading {file}: {str(e)}")
    
    # Combine all dataframes into a single dataframe
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Trim the 'mobile' and 'whatsapp' columns to remove +91- from the beginning
        if 'mobile' in combined_df.columns:
            combined_df['mobile'] = combined_df['mobile'].astype(str).str.replace(r'^\+91-', '', regex=True)
            logger.info("Trimmed +91- prefix from mobile numbers")
        
        if 'whatsapp' in combined_df.columns:
            combined_df['whatsapp'] = combined_df['whatsapp'].astype(str).str.replace(r'^\+91-', '', regex=True)
            logger.info("Trimmed +91- prefix from whatsapp numbers")
        
        # Sort the combined dataframe by the 'id' field
        if 'id' in combined_df.columns:
            combined_df = combined_df.sort_values(by='id')
            logger.info(f"Combined dataframe has {len(combined_df)} rows and {combined_df.shape[1]} columns (sorted by id)")
        else:
            logger.warning(f"Combined dataframe has {len(combined_df)} rows and {combined_df.shape[1]} columns (id column not found for sorting)")
    else:
        logger.warning("No valid dataframes to combine.")
        combined_df = pd.DataFrame()

# Display the first few rows of the combined dataframe
if not combined_df.empty:
    logger.info("\nFirst few rows of the combined dataframe:")
    logger.info(combined_df.head())
    user_input = input("Press s to save: \t")
    if user_input == "s":
        combined_df.to_excel("data/final_candidates.xlsx", index=False)
        logger.info("Saved combined dataframe to data/final_candidates.xlsx")
    else:
        logger.warning("Not saving the combined dataframe.")
