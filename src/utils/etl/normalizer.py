"""
Data normalization and standardization module.

This module contains the DataNormalizer class, which is responsible for:
- Text preprocessing
- Matching and standardizing roles, skills, and levels using various strategies
- Providing a consistent interface for data normalization
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union

import numpy as np
import pandas as pd
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.defs import ROLES, LEVELS, SKILLS, ROLE_MAPPING, LEVEL_MAPPING, SKILL_MAPPING, CITIES

# Configure logger
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


def is_valid_mobile(num):
    """
    Validates if a mobile number is in the correct format:
    +[country code]-[10 digits]
    """
    if num is None:
        return False
    
    pattern = r'^\+\d{1,3}-\d{10}$'
    return bool(re.match(pattern, str(num)))

def is_valid_email(email):
    """
    Validates email addresses to ensure they:
    - Follow standard email format
    - Don't contain common typos
    - Have valid TLD length
    """
    if email is None:
        return False
    
    email = str(email)
    
    # More comprehensive email pattern
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    
    # Additional validations
    if '..' in email:
        return False
    
    # Check TLD length (2-63 characters as per standards)
    tld = email.split('.')[-1]
    if len(tld) < 2 or len(tld) > 63:
        return False
    
    # Common typo check
    common_typos = ['gmial', 'yahho', 'outlok', 'hotnail']
    domain = email.split('@')[1].split('.')[0].lower()
    for typo in common_typos:
        if typo in domain:
            return False
    
    return True

def is_valid_pin(pin):
    """
    Validates if a PIN code is 6 digits long.
    """
    if pin is None:
        return False
    
    pin_str = str(pin).strip()
    return pin_str.isdigit() and len(pin_str) == 6

def is_valid_date(date):
    """
    Validates if a date is in the format DD/MM/YYYY.
    """
    if date is None:
        return False
    
    date_str = str(date).strip()
    
    # Check basic format
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        return False
    
    # Additional validation could check if it's a valid calendar date
    try:
        day, month, year = map(int, date_str.split('/'))
        # Basic range checks
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1000 <= year <= 9999):
            return False
    except ValueError:
        return False
    
    return True


class DataNormalizer:
    """
    The DataNormalizer class is responsible for standardizing and normalizing
    text data like roles, skills, and education levels. It uses multiple
    matching strategies to find the best standardization.
    """
    
    def __init__(self, roles: List[str] = ROLES, 
                 levels: List[str] = LEVELS, 
                 skills: List[str] = SKILLS,
                 cities: List[str] = CITIES):
        """
        Initialize the DataNormalizer with reference data.
        
        Args:
            roles: List of standard role names
            levels: List of standard education/job levels
            skills: List of standard skills
        """
        try:
            self.roles = roles
            self.levels = levels
            self.skills = skills
            self.cities = cities
            self.role_patterns = ROLE_MAPPING
            self.level_patterns = LEVEL_MAPPING
            self.skill_patterns = SKILL_MAPPING
            
            # Prepare TF-IDF vectorizer for semantic matching
            self.skill_vectorizer = TfidfVectorizer()
            self.skill_matrix = self.skill_vectorizer.fit_transform(self.skills)
            
            self.role_vectorizer = TfidfVectorizer()
            self.role_matrix = self.role_vectorizer.fit_transform(self.roles)
            
            logger.info("DataNormalizer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DataNormalizer: {e}", exc_info=True)
            raise
    
    def _preprocess_text(self, text: Any) -> str:
        """
        Clean and normalize text for better matching.
        
        Args:
            text: Input text to preprocess
            
        Returns:
            Preprocessed text string
        """
        try:
            if pd.isna(text) or not isinstance(text, str):
                return ""
            # Convert to lowercase, remove extra spaces
            text = re.sub(r'\s+', ' ', str(text).lower().strip())
            # Remove special characters but keep spaces
            text = re.sub(r'[^\w\s]', ' ', text)
            return text
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}", exc_info=True)
            return ""
    
    def _direct_match(self, input_text: str, target_list: List[str]) -> Optional[str]:
        """
        Perform direct string matching against a list of targets.
        
        Args:
            input_text: Input text to match
            target_list: List of target strings to match against
            
        Returns:
            Matched string or None if no match found
        """
        try:
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
        except Exception as e:
            logger.error(f"Error in direct matching: {e}", exc_info=True)
            return None
    
    def _regex_match(self, input_text: str, pattern_dict: Dict[str, str]) -> Optional[str]:
        """
        Match input text against regex patterns in a dictionary.
        
        Args:
            input_text: Input text to match
            pattern_dict: Dictionary mapping regex patterns to result strings
            
        Returns:
            Matched result string or None if no match found
        """
        try:
            if not input_text:
                return None
                
            for pattern, result in pattern_dict.items():
                if re.search(pattern, input_text, re.IGNORECASE):
                    return result
                    
            return None
        except Exception as e:
            logger.error(f"Error in regex matching: {e}", exc_info=True)
            return None
    
    def _fuzzy_match(self, input_text: str, target_list: List[str], threshold: int = 75) -> Optional[str]:
        """
        Find best fuzzy match in target list.
        
        Args:
            input_text: Input text to match
            target_list: List of target strings to match against
            threshold: Minimum score (0-100) for a match to be considered valid
            
        Returns:
            Best fuzzy-matched string or None if no match meets the threshold
        """
        try:
            if not input_text or len(input_text) < 3:
                return None
                
            best_match = process.extractOne(input_text, target_list)
            if best_match and best_match[1] >= threshold:
                return best_match[0]
                
            return None
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}", exc_info=True)
            return None
    
    def _vector_similarity_match(self, input_text: str, is_role: bool = False) -> Optional[str]:
        """
        Find best semantic match using TF-IDF and cosine similarity.
        
        Args:
            input_text: Input text to match
            is_role: Whether matching against roles (True) or skills (False)
            
        Returns:
            Best semantically matched string or None if no good match found
        """
        try:
            if not input_text or len(input_text) < 3:
                return None
                
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
            logger.error(f"Vector similarity matching error: {e}", exc_info=True)
            
        return None

    def match_city(self, city: str, state: str = None) -> str:
        """
        Match input text to a standardized city.
        
        Args:
            city: Input text to match against standard cities using fuzzy matching
            
        """
        try:
            preprocessed = self._preprocess_text(city)
            if not preprocessed or len(preprocessed) < 3:
                logger.warning(f"Input text {city} is too short: {city}")
                return None
            if state is not None and state != "Andhra Pradesh":
                target = self.cities[self.cities["state"] == state]["name"].to_list()
            else:
                target = self.cities["name"].to_list()
            best_match = process.extractOne(preprocessed, target)
            if best_match and best_match[1] >= 70:
                return best_match[0]
                
            return None
        except Exception as e:
            logger.error(f"Error matching city: {e}", exc_info=True)
            return None

    def match_role(self, input_text: str, strategy: str = 'progressive') -> str:
        """
        Match input text to a standardized role.
        
        Args:
            input_text: Input text to match against standard roles
            strategy: Matching strategy to use, one of:
                    'direct' - Direct string matching
                    'regex' - Regular expression matching
                    'fuzzy' - Fuzzy string matching
                    'vector' - Vector similarity matching
                    'progressive' - Try all strategies in order of increasing cost
            
        Returns:
            Standardized role string or None if no match found
        """
        try:
            preprocessed = self._preprocess_text(input_text)
            
            if not preprocessed:
                return None
                
            if strategy == 'direct':
                return self._direct_match(preprocessed, self.roles) or None
            elif strategy == 'regex':
                return self._regex_match(preprocessed, self.role_patterns) or None
            elif strategy == 'fuzzy':
                return self._fuzzy_match(preprocessed, self.roles) or None
            elif strategy == 'vector':
                return self._vector_similarity_match(preprocessed, is_role=True) or None
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
                    
                return None
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        except Exception as e:
            logger.error(f"Error matching role: {e}", exc_info=True)
            return None
    
    def match_level(self, input_text: str, strategy: str = 'regex') -> Optional[str]:
        """
        Match input text to a standardized level.
        
        Args:
            input_text: Input text to match against standard levels
            strategy: Matching strategy to use (default: 'regex')
            
        Returns:
            Standardized level string or "NA" if no match found
        """
        try:
            preprocessed = self._preprocess_text(input_text)
            
            if not preprocessed:
                return None
                
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
                    
            return None
        except Exception as e:
            logger.error(f"Error matching level: {e}", exc_info=True)
            return None
    
    def match_skill(self, input_text: str, strategy: str = 'progressive') -> str:
        """
        Match input text to standardized skills.
        
        Args:
            input_text: Input text to match against standard skills
            strategy: Matching strategy to use (default: 'progressive')
            
        Returns:
            Standardized skill string or None if no match found
        """
        try:
            preprocessed = self._preprocess_text(input_text)
            
            if not preprocessed:
                return None
                
            if strategy == 'direct':
                return self._direct_match(preprocessed, self.skills) or None
            elif strategy == 'regex':
                return self._regex_match(preprocessed, self.skill_patterns) or None
            elif strategy == 'fuzzy':
                return self._fuzzy_match(preprocessed, self.skills) or None
            elif strategy == 'vector':
                return self._vector_similarity_match(preprocessed) or None
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
                    
                return None
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        except Exception as e:
            logger.error(f"Error matching skill: {e}", exc_info=True)
            return None
        
    def sanitize_number(self, number: int) -> str:
        """
        Sanitize a number by removing non-numeric characters and standardizing the format.
        
        Args:
            number: Input number string to sanitize
            
        Returns:
            Sanitized number string
        """
        try:
            if pd.isna(number) or not isinstance(number, Union[int, str]):
                return None
            
            if number is None:
                return None
            
            # Convert to string if not already
            number = str(number)
            
            # Remove all whitespace and special characters
            new_num = re.sub(r'[\s\-\(\)\+]', '', number)

        # Check if it's an Indian number (10 digits with optional 91 prefix)
            if len(new_num) == 10 and new_num.startswith(('6', '7', '8', '9')):
                # Add the country code if it's just 10 digits
                return f"+91-{new_num}"
            elif len(new_num) == 12 and new_num.startswith('91') and new_num[2:].startswith(('6', '7', '8', '9')):
                # Format with proper prefix if it has country code
                return f"+91-{new_num[2:]}"
            elif len(new_num) == 11 and new_num.startswith('0') and new_num[1:].startswith(('6', '7', '8', '9')):
                # Handle numbers starting with 0
                return f"+91-{new_num[1:]}"
            else:
                # If we can't confidently format it, return the original
                logger.warning(f"Failed to sanitise mobile number: {number}")
                return number
        except Exception as e:
            logger.error(f"Error sanitizing number: {e}", exc_info=True)
            return None
            
    def sanitize_email(self, email: Optional[str]) -> Optional[str]:
        """
        Sanitizes email addresses by:
        - Converting to lowercase
        - Removing leading/trailing whitespace
        - Removing dots from Gmail addresses before the @ symbol
        - Removing any plus addressing (e.g., user+tag@example.com → user@example.com)
        - Standardizing common domain typos
        
        Args:
            email: Input email string to sanitize
            
        Returns:
            Sanitized email string
        """
        try:
            if email is None:
                return None
                
            if pd.isna(email) or not isinstance(email, str):
                return None
                
            # Check basic email validity
            if not is_valid_email(email):
                logger.warning(f"Invalid email format: {email}")
                return email
            
            # Basic sanitization
            email = email.strip().lower()
            
            # Split email into local part and domain
            if '@' in email:
                local_part, domain = email.split('@', 1)
                
                # Handle Gmail dot removal (dots in local part are ignored by Gmail)
                if domain == 'gmail.com':
                    local_part = local_part.replace('.', '')
                
                # Remove plus addressing (everything between + and @)
                if '+' in local_part:
                    local_part = local_part.split('+', 1)[0]
                
                # Fix common domain typos
                domain_fixes = {
                    'gmial.com': 'gmail.com',
                    'gmal.com': 'gmail.com',
                    'gmail.co': 'gmail.com',
                    'gmail.comm': 'gmail.com',
                    'yahho.com': 'yahoo.com',
                    'yaho.com': 'yahoo.com',
                    'yahoo.comm': 'yahoo.com',
                    'hotmial.com': 'hotmail.com',
                    'hotnail.com': 'hotmail.com',
                    'hotmail.comm': 'hotmail.com',
                    'outlok.com': 'outlook.com',
                    'outloo.com': 'outlook.com',
                    'outlook.comm': 'outlook.com'
                }
                
                if domain in domain_fixes:
                    domain = domain_fixes[domain]
                
                # Fix any domain ending with .comm
                if domain.endswith('.comm'):
                    domain = domain[:-1]
                
                email = f"{local_part}@{domain}"
            
            return email
        except Exception as e:
            logger.error(f"Error sanitizing email: {e}", exc_info=True)
            return None
            
    def normalize_row(self, row: Union[Dict, pd.Series], strategy: str = 'progressive') -> Dict[str, str]:
        """
        Process a single row to extract role, level, and skill.
        
        Args:
            row: Row data containing primary skill information
            strategy: Matching strategy to use
            
        Returns:
            Dictionary with normalized skill, role, and level values
        """
        try:
            skill = str(row["skill"]) if "skill" in row else ""
            city = str(row["old_city"]) if "old_city" in row else ""
            state = str(row["state"]) if "state" in row else ""
            
            # Extract and sanitize mobile number if it exists
            mobile = row.get("old_mobile", None)
            if mobile is not None:
                sanitized_mobile = self.sanitize_number(mobile)
            else:
                sanitized_mobile = None
                
            # Extract and sanitize whatsapp number if it exists
            whatsapp = row.get("old_whatsapp", None)
            if whatsapp is not None:
                sanitized_whatsapp = self.sanitize_number(whatsapp)
            else:
                sanitized_whatsapp = None
                
            # Extract and sanitize email if it exists
            email = row.get("old_email", None)
            if email is not None:
                sanitized_email = self.sanitize_email(email)
            else:
                sanitized_email = None

            if not skill or pd.isna(skill) or skill.strip() == "":
                return {
                    "skill": None, 
                    "role": None, 
                    "level": None,
                    "city": self.match_city(city, state) if city else None,
                    "mobile": sanitized_mobile,
                    "whatsapp": sanitized_whatsapp,
                    "email": sanitized_email
                }
            
            # First attempt to match level since it's often part of the title
            level = self.match_level(skill, strategy)
            
            # Match the role
            role = self.match_role(skill, strategy)
            
            # Match the skill
            sanitized_skill = self.match_skill(skill, strategy)
            
            new_city = self.match_city(city, state)

            return {
                "skill": sanitized_skill,
                "role": role,
                "level": level,
                "city": new_city,
                "mobile": sanitized_mobile,
                "whatsapp": sanitized_whatsapp,
                "email": sanitized_email
            }
        except Exception as e:
            logger.error(f"Error processing row: {e}", exc_info=True)
            return {"skill": None, "role": None, "level": None, "city": None, "mobile": None, "whatsapp": None, "email": None} 
