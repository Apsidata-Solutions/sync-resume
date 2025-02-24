import re
import time
import warnings
from functools import partial
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from defs import ROLES, LEVELS, SKILLS, ROLE_MAPPING, LEVEL_MAPPING, SKILL_MAPPING
warnings.filterwarnings('ignore')

class SkillMatcher:
    def __init__(self, roles=ROLES, levels=LEVELS, skills=SKILLS):
        self.roles = roles
        self.levels = levels
        self.skills = skills
        self.role_patterns = ROLE_MAPPING
        self.level_patterns = LEVEL_MAPPING
        self.skill_patterns = SKILL_MAPPING
        
        # Prepare TF-IDF vectorizer for semantic matching
        self.skill_vectorizer = TfidfVectorizer()
        self.skill_matrix = self.skill_vectorizer.fit_transform(self.skills)
        
        self.role_vectorizer = TfidfVectorizer()
        self.role_matrix = self.role_vectorizer.fit_transform(self.roles)
        
    def _preprocess_text(self, text):
        """Clean and normalize text for better matching"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        # Convert to lowercase, remove extra spaces
        text = re.sub(r'\s+', ' ', str(text).lower().strip())
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        return text
    
    def _direct_match(self, input_text, target_list):
        """Perform direct string matching against a list of targets"""
        if not input_text:
            return None
        
        # First try exact match
        cleaned_input = input_text.lower().strip()
        for item in target_list:
            if item.lower() == cleaned_input:
                return item
        
        # Try case-insensitive contains match
        for item in target_list:
            if item.lower() in cleaned_input:
                return item
                
        return None
    
    def _regex_match(self, input_text, pattern_dict):
        """Match input text against regex patterns in a dictionary"""
        if not input_text:
            return None
            
        for pattern, result in pattern_dict.items():
            if re.search(pattern, input_text, re.IGNORECASE):
                return result
                
        return None
    
    def _fuzzy_match(self, input_text, target_list, threshold=75):
        """Find best fuzzy match in target list"""
        if not input_text or len(input_text) < 3:
            return None
            
        best_match = process.extractOne(input_text, target_list)
        if best_match and best_match[1] >= threshold:
            return best_match[0]
            
        return None
    
    def _vector_similarity_match(self, input_text, is_role=False):
        """Find best semantic match using TF-IDF and cosine similarity"""
        if not input_text or len(input_text) < 3:
            return None
            
        try:
            # Choose the appropriate vectorizer and matrix
            if is_role:
                vectorizer = self.role_vectorizer
                matrix = self.role_matrix
                target_list = self.roles
            else:
                vectorizer = self.skill_vectorizer
                matrix = self.skill_matrix
                target_list = self.skills
                
            # Transform input text to vector
            input_vector = vectorizer.transform([input_text])
            
            # Calculate similarity scores
            similarity_scores = cosine_similarity(input_vector, matrix).flatten()
            
            # Find the index of the highest similarity score
            best_idx = np.argmax(similarity_scores)
            
            # Return the best match if similarity is above threshold
            if similarity_scores[best_idx] > 0.3:
                return target_list[best_idx]
                
        except Exception as e:
            print(f"Vector similarity matching error: {e}")
            
        return None
    
    def match_role(self, input_text, strategy='progressive'):
        """
        Match input text to a standardized role
        Strategy options: 'direct', 'regex', 'fuzzy', 'vector', 'progressive'
        """
        preprocessed = self._preprocess_text(input_text)
        
        if not preprocessed:
            return "Unknown"
            
        if strategy == 'direct':
            return self._direct_match(preprocessed, self.roles) or "Unknown"
        elif strategy == 'regex':
            return self._regex_match(preprocessed, self.role_patterns) or "Unknown"
        elif strategy == 'fuzzy':
            return self._fuzzy_match(preprocessed, self.roles) or "Unknown"
        elif strategy == 'vector':
            return self._vector_similarity_match(preprocessed, is_role=True) or "Unknown"
        elif strategy == 'progressive':
            # Try strategies in order of increasing computational cost
            result = self._direct_match(preprocessed, self.roles)
            if result:
                return result
                
            result = self._regex_match(preprocessed, self.role_patterns)
            if result:
                return result
                
            result = self._fuzzy_match(preprocessed, self.roles)
            if result:
                return result
                
            result = self._vector_similarity_match(preprocessed, is_role=True)
            if result:
                return result
                
            return "Unknown"
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def match_level(self, input_text, strategy='regex'):
        """Match input text to a standardized level"""
        preprocessed = self._preprocess_text(input_text)
        
        if not preprocessed:
            return "NA"
            
        # For levels, regex matching is usually sufficient
        result = self._regex_match(preprocessed, self.level_patterns)
        if result:
            return result
            
        # Check for common abbreviations
        if re.search(r'\bprt\b', preprocessed, re.IGNORECASE):
            return "Primary (PRT)"
        elif re.search(r'\btgt\b', preprocessed, re.IGNORECASE):
            return "TGT"
        elif re.search(r'\bpgt\b', preprocessed, re.IGNORECASE):
            return "PGT"
            
        # Use fuzzy matching as fallback
        if strategy == 'fuzzy' or strategy == 'progressive':
            fuzzy_result = self._fuzzy_match(preprocessed, self.levels)
            if fuzzy_result:
                return fuzzy_result
                
        return "NA"
    
    def match_skill(self, input_text, strategy='progressive'):
        """
        Match input text to standardized skills
        Returns the primary skill identified
        """
        preprocessed = self._preprocess_text(input_text)
        
        if not preprocessed:
            return "Unknown"
            
        if strategy == 'direct':
            return self._direct_match(preprocessed, self.skills) or "Unknown"
        elif strategy == 'regex':
            return self._regex_match(preprocessed, self.skill_patterns) or "Unknown"
        elif strategy == 'fuzzy':
            return self._fuzzy_match(preprocessed, self.skills) or "Unknown"
        elif strategy == 'vector':
            return self._vector_similarity_match(preprocessed) or "Unknown"
        elif strategy == 'progressive':
            # Try strategies in order from simple to complex
            result = self._direct_match(preprocessed, self.skills)
            if result:
                return result
                
            result = self._regex_match(preprocessed, self.skill_patterns)
            if result:
                return result
                
            result = self._fuzzy_match(preprocessed, self.skills)
            if result:
                return result
                
            result = self._vector_similarity_match(preprocessed)
            if result:
                return result
                
            return "Unknown"
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

def process_single_row(row, matcher, strategy='progressive'):
    """Process a single row to extract role, level, and skill"""
    primary_skill = str(row['Primary Skill']) if 'Primary Skill' in row else ""
    
    if not primary_skill or pd.isna(primary_skill) or primary_skill.strip() == "":
        return {"Skill": "Unknown", "Role": "Unknown", "Level": "NA"}
    
    # First attempt to match level since it's often part of the title
    level = matcher.match_level(primary_skill, strategy)
    
    # Match the role
    role = matcher.match_role(primary_skill, strategy)
    
    # Match the skill
    skill = matcher.match_skill(primary_skill, strategy)
    
    return {
        "Skill": skill,
        "Role": role,
        "Level": level
    }

def process_dataframe(df, matcher, strategy='progressive', num_workers=4):
    """Process entire dataframe with parallel execution"""
    start_time = time.time()
    
    # Create a partial function with the matcher and strategy
    process_func = partial(process_single_row, matcher=matcher, strategy=strategy)
    
    results = []
    
    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all rows for processing
        futures = [executor.submit(process_func, row) for _, row in df.iterrows()]
        
        # Collect results as they complete
        for future in futures:
            results.append(future.result())
    
    # Convert results to DataFrame
    result_df = pd.DataFrame(results)
    
    # Add results back to original dataframe
    df_result = pd.concat([df.reset_index(drop=True), result_df], axis=1)
    
    end_time = time.time()
    print(f"Processing completed in {end_time - start_time:.2f} seconds")
    
    return df_result

def test_sample(file_path, sample_size=100, strategy='progressive'):
    """Test the algorithm on a sample of data"""
    try:
        print(f"Loading data from {file_path}...")
        df = pd.read_excel(file_path, sheet_name="Sheet1")
        
        if 'Primary Skill' not in df.columns:
            print("Error: Column 'Primary Skill' not found in the Excel sheet.")
            return None
            
        print(f"Data loaded successfully. Total rows: {len(df)}")
        
        # Take a sample
        sample = df.sample(min(sample_size, len(df)))
        print(f"Processing sample of {len(sample)} rows...")
        
        # Initialize matcher
        matcher = SkillMatcher()
        
        # Process the sample
        result = process_dataframe(sample, matcher, strategy=strategy)
        
        return result
    
    except Exception as e:
        print(f"Error processing sample: {e}")
        return None

def run_full_processing(file_path, output_path=None, strategy='progressive', num_workers=None):
    """Run the full processing on all data and generate a report"""
    try:
        print(f"Loading data from {file_path}...")
        df = pd.read_excel(file_path, sheet_name="Sheet1")
        df.drop(columns=["Level"], inplace=True)
        
        if 'Primary Skill' not in df.columns:
            print("Error: Column 'Primary Skill' not found in the Excel sheet.")
            return None
            
        total_rows = len(df)
        print(f"Data loaded successfully. Total rows: {total_rows}")
        
        # Initialize matcher
        matcher = SkillMatcher()
        
        # Process all data
        print(f"Processing all {total_rows} rows with strategy: {strategy}...")
        result = process_dataframe(df, matcher, strategy=strategy, num_workers=num_workers)
        
        # Check if result is None
        if result is None:
            print("Error: No results returned from processing.")
            return None, None
        
        # Generate report
        report = generate_matching_report(result)
        
        # Save results if output path is provided
        if output_path:
            result.to_excel(output_path, index=False)
            print(f"Results saved to {output_path}")
        
        return result, report
    
    except Exception as e:
        print(f"Error in full processing: {e}")
        return None, None

def generate_matching_report(df):
    """Generate a report on the matching results"""
    total_rows = len(df)
    
    # Count known vs unknown
    unknown_skills = (df['Skill'] == 'Unknown').sum()
    unknown_roles = (df['Role'] == 'Unknown').sum()
    
    # Get distribution of roles, levels, and skills
    role_counts = df['Role'].value_counts()
    level_counts = df['Level'].value_counts()
    skill_counts = df['Skill'].value_counts()
    
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
    
    return report

def compare_strategies(file_path, sample_size=100):
    """Compare different matching strategies on a sample"""
    df = pd.read_excel(file_path, sheet_name="Sheet1")
    sample = df.sample(min(sample_size, len(df)))
    
    strategies = ['direct', 'regex', 'fuzzy', 'vector', 'progressive']
    results = {}
    times = {}
    
    matcher = SkillMatcher()
    
    for strategy in strategies:
        print(f"Testing strategy: {strategy}")
        start_time = time.time()
        result = process_dataframe(sample, matcher, strategy=strategy)
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
    
    return pd.DataFrame(results).T

# Main interface function
def process_candidate_skills(file_path, mode='test', sample_size=100, strategy='progressive', 
                          output_path=None, num_workers=None):
    """
    Main function to process candidate skills
    
    Parameters:
    - file_path: Path to the Excel file
    - mode: 'test' for sample testing, 'full' for full processing, 'compare' to compare strategies
    - sample_size: Number of rows to sample for testing
    - strategy: Matching strategy to use ('direct', 'regex', 'fuzzy', 'vector', 'progressive')
    - output_path: Path to save output Excel file (only used in 'full' mode)
    - num_workers: Number of parallel workers (None = auto)
    
    Returns:
    - DataFrame with results, or comparison report if mode='compare'
    """
    if mode == 'test':
        return test_sample(file_path, sample_size, strategy)
    elif mode == 'full':
        result, report = run_full_processing(file_path, output_path, strategy, num_workers)
        print("\nMatching Report:")
        print(f"Total records processed: {report['summary']['total_records']}")
        print(f"Skills identification rate: {report['summary']['identification_rate_skills']:.2f}%")
        print(f"Roles identification rate: {report['summary']['identification_rate_roles']:.2f}%")
        print("\nTop 5 identified skills:")
        for skill, count in list(report['top_skills'].items())[:5]:
            print(f"  - {skill}: {count}")
        return result
    elif mode == 'compare':
        return compare_strategies(file_path, sample_size)
    else:
        print(f"Unknown mode: {mode}. Use 'test', 'full', or 'compare'.")
        return None

# Example usage:
if __name__ == "__main__":
    # # Test sample of data
    # result = process_candidate_skills('data/Candidates.xlsx', mode='test', sample_size=500)
    # print(result[["Id", "Primary Skill","Skill", "Role", "Level"]])
    # result.to_excel("data/Processed Candidates_Test.xlsx", index=False)

    # Run full processing
    result = process_candidate_skills('data/Candidates.xlsx', mode='full', output_path='data/Processed Candidates.xlsx')
    print(result.head(10))
    # # Compare different strategies
    # comparison = process_candidate_skills('data/Candidates.xlsx', mode='compare', sample_size=100)
    # print(comparison)
    