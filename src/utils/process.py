# Import system modules first
import os
import sys

# sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import time
import random
import io
import asyncio
from pathlib import Path
import argparse
import logging

import uuid
import zipfile
import pandas as pd
import httpx    
import requests
from typing import Optional
from pydantic import BaseModel

from fastapi import UploadFile

from src.routes.resume import batch_load

logger = logging.getLogger(__name__)

# Ensure logs directory exists before creating file handler
# os.makedirs('logs', exist_ok=True)
handler = logging.FileHandler('logs/process.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger.setLevel(logging.INFO)

class Batch(BaseModel):
    id: str
    status: bool
    data: pd.DataFrame
    
    model_config = {
        "arbitrary_types_allowed": True
    }

def get_unprocessed_files(input_dir:str = "data/preprocessed", output_dir:str = "data/processed") -> list[Batch]:
    """
    Identifies files in the input directory that are not yet in the output directory.
    Args:
        input_dir (str): Path to the input directory, defaults to "data/preprocessed"
        output_dir (str): Path to the output directory, defaults to "data/processed"
    Returns:
        list: Names of files that need to be processed
    """
    # Define the paths to the directories
    preprocessed_dir = Path(input_dir)
    processed_dir = Path(output_dir)
    
    # Ensure the directories exist
    if not preprocessed_dir.exists() :
        logger.warning(f"Warning: Directory {preprocessed_dir} does not exist")
        return []
    
    if not processed_dir.exists():
        logger.warning(f"Warning: Directory {processed_dir} does not exist, creating it")
        os.makedirs(processed_dir)   
    
    # Get lists of files in both directories
    preprocessed_files = {f.name for f in preprocessed_dir.iterdir() if f.is_file()}
    processed_files = {f.name for f in processed_dir.iterdir() if f.is_file()}
    
    # Find files that are in preprocessed but not in processed
    unprocessed_files = preprocessed_files - processed_files
    
    # Print the unprocessed files
    if unprocessed_files:
        logger.info(f"Found {len(unprocessed_files)} unprocessed files:")
        for filename in unprocessed_files:
            logger.debug(f"  - {filename}")
    else:
        logger.info("All files have been processed.")

    batches = [{"id":file , "status":False, "data":pd.read_csv(f"{input_dir}/{file}")} for file in unprocessed_files]

    return batches

def split(df:pd.DataFrame, batch_size:int = 80, save_dir:Optional[str] = None) -> list[Batch]:
    """
    Splits a dataframe into a list of batches of a given size. Optionally saves the batches to a directory.
    """
    try:
        if "status" not in df.columns:  
            logger.error("Status column not found in dataframe")
            raise ValueError("Status column not found in dataframe. Cant split dataframe")
        
        logger.info(f"Splitting dataframe of size {df.shape[0]} into batches of size {batch_size}")
        filtered_df = df[df["status"]==0]
        batches = [Batch(id="batch-"+str(uuid.uuid4()), status=False, data=filtered_df.iloc[i:i+batch_size]) for i in range(0, len(filtered_df), batch_size)]
        if save_dir:
            for batch in batches:
                if not os.path.exists(save_dir):
                    logger.debug(f"Directory {save_dir} does not exist, creating it")
                    os.makedirs(save_dir)

                batch.data.to_csv(f"{save_dir}/{batch.id}.csv", index=False)
                logger.debug(f"Saved batch {batch.id} to {save_dir}")
        return batches
    except Exception as e:
        logger.error(f"Error splitting dataframe: {str(e)}")
        return []

def create_resume_zip(batch:pd.DataFrame):
    """
    Creates a ZIP file containing resumes downloaded from URLs.
    
    Args:
        batch_urls (pd.DataFrame): DataFrame containing resume Id, URL and status
        
    Returns:
        UploadFile: FastAPI UploadFile object containing the zipped resumes
    """
    required_columns = ["status", "resume", "id"]
    for column in required_columns:
        if column not in batch.columns:
            logger.error(f"{column.capitalize()} column not found in batch")
            return None, None
    
    logger.info(f"Creating zip file for batch of {len(batch)} resumes")
    
    zip_buffer = io.BytesIO()
    ids = []
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        
        for id, url, status in zip(batch.id, batch.resume, batch.status):
            fileName = url.split("/")[-1]
            if status!=0:
                logger.info(f"Skipping file {fileName} due to status {status}")
                continue
            try:
                name, ext = fileName.split(".")
                logger.info(f"Processing file: {fileName}")
            except:
                name, ext = fileName, ""
                logger.warning(f"Could not split filename {fileName} into name and extension")

            # Get the resume content
            try:
                response = requests.get(url, timeout=10)
                # Add PDF to zip file
                zip_file.writestr(fileName, response.content)
                ids.append(id)
                logger.info(f"Successfully added {fileName} to zip")
            except Exception as e:
                logger.error(f"Error reading PDF from {url}: {str(e)}")
                continue

    # Create an UploadFile object from the zip buffer
    zip_buffer.seek(0)
    zip_file = UploadFile(
        file=zip_buffer,
        filename="resumes.zip"
    )
    logger.info(f"Successfully created zip file with {len(ids)} resumes")
    return ids, zip_file


async def acreate_resume_zip(batch):
    """
    Creates a ZIP file containing resumes downloaded from URLs concurrently.
    
    Args:
        batch_urls (pd.Series): Series containing resume URLs
        
    Returns:
        UploadFile: FastAPI UploadFile object containing the zipped resumes
    """
    logger.info(f"Creating zip file for batch of {len(batch)} resumes")
    
    zip_buffer = io.BytesIO()
    ids = []
    client = httpx.AsyncClient()
    
    async def download_file(id, url, status):
        """Helper function to download a single file"""
        fileName = url.split("/")[-1]
        if status!=0:
            logger.info(f"Skipping file {fileName} due to status {status}")
            return {
                'success': False,
                'id': id,
                'fileName': fileName
            }
        try:
            name, ext = fileName.split(".")
            logger.info(f"Processing file: {fileName}")
        except:
            name, ext = fileName, ""
            logger.warning(f"Could not split filename {fileName} into name and extension")
            
        try:
            response = await client.get(url, timeout=10)
            return {
                'success': True,
                'id': id,
                'fileName': fileName,
                'content': response.content
            }
        except Exception as e:
            logger.error(f"Error reading PDF from {url}: {str(e)}")
            return {
                'success': False,
                'id': id,
                'fileName': fileName
            }

    # Create download tasks for all URLs
    download_tasks = [download_file(id, url) for id, url in zip(batch.id, batch.resume)]
    
    # Download all files concurrently
    results = await asyncio.gather(*download_tasks)
    
    # Close the client after all downloads are complete
    await client.aclose()
    
    # Write successful downloads to zip file
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for result in results:
            if result['success']:
                zip_file.writestr(result['fileName'], result['content'])
                ids.append(result['id'])
                logger.info(f"Successfully added {result['fileName']} to zip")

    # Create an UploadFile object from the zip buffer
    zip_buffer.seek(0)
    zip_file = UploadFile(
        file=zip_buffer,
        filename="resumes.zip"
    )
    logger.info(f"Successfully created zip file with {len(ids)} resumes")
    return ids, zip_file


def update_candidates_from_response(response, df):
    """Updates 'df' dataframe in-place with values from response
    
    Args:
        response: List of dicts containing candidate data
        df: pandas DataFrame to update
        
    Returns:
        None - updates df in-place
    """
    # DataFrame is mutable so changes are made in-place
    for r in response:
        updated_keys=[]
        if "candidate" not in r:
            logger.warning(f"Not updating {r['id']} due to {r['error']}")
            df.loc[df["id"]==int(r["id"]), "status"] = 2     # 2: Failed
            continue
        for key, value in r["candidate"].items():
            if key in df.columns:
                try:
                    df.loc[df["id"]==int(r["id"]),key]=value
                    updated_keys.append(key)
                except ValueError:
                    df.loc[df["id"]==int(r["id"]),key]=str(value)
                    updated_keys.append(key)
                except Exception as e:
                    logger.error(str(e))

        df.loc[df["id"]==int(r["id"]), "status"] = 1     # 1: Success
        logger.info(f"Updated id: {r["id"]} with keys: {updated_keys}")

        return df



async def main():
    """Main entry point for processing resumes."""


    parser = argparse.ArgumentParser(description="Run script on input file.")
    parser.add_argument('-i', '--input-dir', help="Path to the input file")
    parser.add_argument('-o', '--output-dir', help="Path to the output file")

    args = parser.parse_args()

    if not args.input_dir:
        logger.warning("No input directory provided, using default value: ./data/preprocessed")
    if not args.output_dir:
        logger.warning("No output directory provided, using default value: ./data/processed")

    continue_processing = input("Do you want to continue? (y/n): ")
    if continue_processing != "y":
        logger.warning("Aborting processing")
        return
    
    #First get the unprocessed files
    batches = get_unprocessed_files(args.input_dir or "data/preprocessed", args.output_dir or "data/processed")

    #  Proceed with batch processing on found files
    for idx, batch in enumerate(batches):
        user_input = input(f"Start processing batch {batch['id']}? [ Press Enter to continue, q to quit]")
        if user_input == "q":
            break

        time.sleep(5)

        start_time = time.time()
        logger.info(f"Processing batch {idx+1}\n with id {batch['id']}", "="*40, '\n')

        if batch["status"]:
            logger.info("Skipping batch: ",batch["id"], ": Already processed")
            continue
        
        # First try block - Create zip file
        try:
            ids, zip_file = create_resume_zip(batch["data"])
            if len(ids)==0:
                logger.warning(f"No valid resumes found in {batch['id']}, skipping...")
                continue
        except Exception as e:
            logger.error(f"Error creating zip file for {batch['id']}: {str(e)}")
            continue

        # Second try block - Process batch
        try:
            response = await batch_load(ids, zip_file)
            logger.debug(f"Response: {response}")
        except Exception as e:
            logger.error(f"Error processing {batch['id']}: {str(e)}")
            continue

        # Third try block - Update candidates
        try:
            update_candidates_from_response(response, batch["data"])
        except Exception as e:
            logger.error(f"Error updating candidates for {batch['id']}: {str(e)}")
            continue

        end_time = time.time()
        logger.info(f"Batch {idx+1} processed successfully in {end_time - start_time:.2f} seconds\n")
        batch["data"].to_csv(f"data/processed/{batch['id']}.csv", index=False)
        
    # Uncomment more code as needed
    logger.info("Main function executed successfully!")


if __name__ == "__main__":
    asyncio.run(main())

# %%
