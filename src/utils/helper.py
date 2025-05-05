import re
from typing import Optional

def is_valid_mobile(num):
    """
    Validates if a mobile number is in the correct format:
    +[country code]-[10 digits]
    """
    if num is None:
        return False
    
    pattern = r'^\+\d{1,3}-\d{10}$'
    return bool(re.match(pattern, str(num)))

def sanitise_mobile_number(num):
    """
    Sanitizes and formats mobile numbers to ensure they follow the pattern:
    +[country code]-[10 digits]
    
    Handles various input formats and defaults to Indian country code (+91)
    when appropriate.
    """
    if num is None:
        return None
    
    # Convert to string if not already
    num = str(num)
    
    # Remove all whitespace and special characters
    new_num = re.sub(r'[\s\-\(\)\+]', '', num)
    
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
        print(f"Failed to sanitise mobile number: {num}")
        return num

def sanitise_email(email: Optional[str]) -> Optional[str]:
    """
    Sanitizes email addresses by:
    - Converting to lowercase
    - Removing leading/trailing whitespace
    - Removing dots from Gmail addresses before the @ symbol
    - Removing any plus addressing (e.g., user+tag@example.com → user@example.com)
    - Standardizing common domain typos including extra 'm' in '.comm'
    """
    if email is None:
        return None
    if not (is_valid_email(email)):
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
