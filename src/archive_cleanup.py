import pandas as pd
import re
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from functools import partial
import concurrent.futures

def load_excel_data(file_path, sheet_name):
    """
    Load skills data from Excel file
    """
    print("Loading Excel data...")
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if 'Primary Skill' not in df.columns:
            raise ValueError("Column 'Primary Skill' not found in the Excel sheet")
        print("Excel data loaded successfully.")
        return df['Primary Skill'].dropna().tolist()
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return []

def initialize_master_lists():
    """
    Initialize master lists for roles, levels, and skills
    """
    print("Initializing master lists...")
    # Roles
    roles = [
        "Teacher", "Mother Teacher", "Assistant Teacher",
        "Academic Coordinator", "Head of Department", "Vice Principal/ Headmistress",
        "Principal", "Director", "Events Coordinator", "School Counselor",
        "Admissions Counselor", "School Nurse", "School Doctor", "Sport Coach",
        "Librarian", "Lab Assistant/ Technician", "Front Desk Executive",
        "Clerk/ Office Assistant", "HR Executive", "Finance Executive",
        "Facilities Manager", "Admin Officer", "Marketing Executive",
        "Content Writer", "Graphic Designer", "IT Support Staff",
        "System Admin", "Software Developer", "Analyst", "Canteen Staff",
        "Warden", "Groundsman", "Guard", "Peon", "Bus Driver",
        "Housekeeping Staff", "Maintenance Staff", "Others"
    ]
    
    # Levels
    levels = [
        "Day Care", "Pre-Primary", "Primary (PRT)", 
        "TGT (Trained Graduate Teacher)", "PGT (Post Grad Teacher)",
        "NA", "Other"
    ]
    
    # Skills (subject areas)
    skills = [
        "English", "Hindi", "Sanskrit", "French", "Spanish", "Japanese", "German",
        "Mathematics", "Science", "Physics", "Chemistry", "Biology", 
        "Environmental Science", "Social Science", "History", "Geography",
        "Political Science", "Economics", "Sociology", "Psychology", "Civics",
        "Philosophy", "Commerce", "Accountancy", "Business Studies",
        "Home Science / Family Studies", "Legal Studies", "Library Science",
        "Computer Science", "Vocal Music Classical", "Instrumental Music Classical",
        "Vocal Music Western", "Instrumental Music Western", "Graphics", "Photography",
        "Ceramics", "Woodcraft", "Sculptury", "Dance (Classical)", "Dance (Western)",
        "Arts", "Theatre / Drama", "Robotics", "Fashion", "Photography", "Film Making",
        "Animation", "Debate & Public Speaking", "Creative Writing", "Quiz",
        "General Sport Teacher", "Athletics", "Yoga", "Cricket", "Badminton", "Tennis",
        "Basketball", "Football", "Hockey", "Equestrian", "Squash", "Chess", "Volleyball",
        "Swimming", "Golf", "Table Tennis", "Gymnastics", "Martial Arts", "Shooting",
        "Skating", "Boxing", "Artificial Intelligence", "Web Development",
        "Database Management", "Network Administration", "System Administration",
        "IT Support", "Educational Technology Integration", 
        "Learning Management Systems (LMS) Administration", "Digital Content Creation",
        "Data Analysis", "Data Science", "Cybersecurity", "Video Editing", "Graphic Design",
        "MS Office Suite Proficiency", "School Administration", "Office Management",
        "Event Management", "Facilities Management", "Inventory Management",
        "Front Office Management", "Communication Management", "Finance",
        "Accounts Management", "Human Resources (HR)", "Marketing", "Operations Management",
        "Transport Operations Management", "Hostel Management", "Canteen Management",
        "Security Management", "Housekeeping Management", "Maintenance Management",
        "Laboratory Management"
    ]
    
    print("Master lists initialized.")
    return roles, levels, skills

def create_mapping_dictionaries():
    """
    Create mapping dictionaries for common variations
    """
    print("Creating mapping dictionaries...")
    # Role mappings
    role_mapping = {
        'teacher': 'Teacher',
        'faculty': 'Teacher', 
        'educator': 'Teacher',
        'facilitator': 'Teacher',
        'trainer': 'Teacher',
        'tutor': 'Teacher',
        'lecturer': 'Teacher',
        'professor': 'Teacher',
        'sme': 'Teacher',
        'subject matter expert': 'Teacher',
        'mother teacher': 'Mother Teacher',
        'mommy teacher': 'Mother Teacher',
        'assistant teacher': 'Assistant Teacher',
        'assistant': 'Assistant Teacher',
        'co teacher': 'Assistant Teacher',
        'teaching assistant': 'Assistant Teacher',
        'head': 'Head of Department',
        'hod': 'Head of Department',
        'department head': 'Head of Department',
        'coordinator': 'Academic Coordinator',
        'academic coordinator': 'Academic Coordinator',
        'head coordinator': 'Academic Coordinator',
        'vice principal': 'Vice Principal/ Headmistress',
        'headmistress': 'Vice Principal/ Headmistress',
        'headmaster': 'Vice Principal/ Headmistress',
        'principal': 'Principal',
        'head of school': 'Principal',
        'school head': 'Principal',
        'director': 'Director',
        'event': 'Events Coordinator',
        'event coordinator': 'Events Coordinator',
        'counselor': 'School Counselor',
        'counsellor': 'School Counselor',
        'school counselor': 'School Counselor',
        'psychologist': 'School Counselor',
        'therapist': 'School Counselor',
        'admission': 'Admissions Counselor',
        'admissions': 'Admissions Counselor',
        'admission counselor': 'Admissions Counselor',
        'nurse': 'School Nurse',
        'medical': 'School Nurse',
        'doctor': 'School Doctor',
        'physician': 'School Doctor',
        'coach': 'Sport Coach',
        'sports coach': 'Sport Coach',
        'physical trainer': 'Sport Coach',
        'librarian': 'Librarian',
        'library': 'Librarian',
        'lab assistant': 'Lab Assistant/ Technician',
        'lab technician': 'Lab Assistant/ Technician',
        'laboratory': 'Lab Assistant/ Technician',
        'front desk': 'Front Desk Executive',
        'receptionist': 'Front Desk Executive',
        'front office': 'Front Desk Executive',
        'clerk': 'Clerk/ Office Assistant',
        'office assistant': 'Clerk/ Office Assistant',
        'office admin': 'Clerk/ Office Assistant',
        'administrative assistant': 'Clerk/ Office Assistant',
        'hr': 'HR Executive',
        'human resource': 'HR Executive',
        'human resources': 'HR Executive',
        'hr executive': 'HR Executive',
        'recruiter': 'HR Executive',
        'talent acquisition': 'HR Executive',
        'finance': 'Finance Executive',
        'accounts': 'Finance Executive',
        'accountant': 'Finance Executive',
        'finance executive': 'Finance Executive',
        'facility': 'Facilities Manager',
        'facilities': 'Facilities Manager',
        'admin': 'Admin Officer',
        'administration': 'Admin Officer',
        'administrator': 'Admin Officer',
        'administrative officer': 'Admin Officer',
        'marketing': 'Marketing Executive',
        'digital marketing': 'Marketing Executive',
        'social media': 'Marketing Executive',
        'content': 'Content Writer',
        'content writer': 'Content Writer',
        'content creator': 'Content Writer',
        'copywriter': 'Content Writer',
        'graphic': 'Graphic Designer',
        'designer': 'Graphic Designer',
        'graphic designer': 'Graphic Designer',
        'it support': 'IT Support Staff',
        'tech support': 'IT Support Staff',
        'technical support': 'IT Support Staff',
        'system admin': 'System Admin',
        'system administrator': 'System Admin',
        'network admin': 'System Admin',
        'developer': 'Software Developer',
        'software engineer': 'Software Developer',
        'programmer': 'Software Developer',
        'coder': 'Software Developer',
        'analyst': 'Analyst',
        'data analyst': 'Analyst',
        'business analyst': 'Analyst',
        'research analyst': 'Analyst',
        'canteen': 'Canteen Staff',
        'warden': 'Warden',
        'hostel': 'Warden',
        'groundsman': 'Groundsman',
        'grounds': 'Groundsman',
        'guard': 'Guard',
        'security': 'Guard',
        'security guard': 'Guard',
        'watchman': 'Guard',
        'peon': 'Peon',
        'office boy': 'Peon',
        'attendant': 'Peon',
        'driver': 'Bus Driver',
        'bus driver': 'Bus Driver',
        'transport': 'Bus Driver',
        'housekeeping': 'Housekeeping Staff',
        'cleaner': 'Housekeeping Staff',
        'janitor': 'Housekeeping Staff',
        'maintenance': 'Maintenance Staff',
        'electrician': 'Maintenance Staff',
        'plumber': 'Maintenance Staff',
        'mechanic': 'Maintenance Staff',
    }
    
    # Level mappings
    level_mapping = {
        'daycare': 'Day Care',
        'day care': 'Day Care',
        'nursery': 'Pre-Primary',
        'kindergarten': 'Pre-Primary',
        'kg': 'Pre-Primary',
        'pre primary': 'Pre-Primary',
        'pre-primary': 'Pre-Primary',
        'pre school': 'Pre-Primary',
        'pre-school': 'Pre-Primary',
        'montessori': 'Pre-Primary',
        'play school': 'Pre-Primary',
        'playgroup': 'Pre-Primary',
        'primary': 'Primary (PRT)',
        'prt': 'Primary (PRT)',
        'elementary': 'Primary (PRT)',
        'middle school': 'TGT (Trained Graduate Teacher)',
        'tgt': 'TGT (Trained Graduate Teacher)',
        'trained graduate teacher': 'TGT (Trained Graduate Teacher)',
        'secondary': 'TGT (Trained Graduate Teacher)',
        'high school': 'TGT (Trained Graduate Teacher)',
        'senior secondary': 'PGT (Post Grad Teacher)',
        'pgt': 'PGT (Post Grad Teacher)',
        'post graduate teacher': 'PGT (Post Grad Teacher)',
        'higher secondary': 'PGT (Post Grad Teacher)',
    }
    
    # Skill mappings (focusing on academic subjects and technical skills)
    skill_mapping = {
        'english': 'English',
        'literature': 'English',
        'language': 'English',
        'hindi': 'Hindi',
        'sanskrit': 'Sanskrit',
        'french': 'French',
        'spanish': 'Spanish',
        'japanese': 'Japanese',
        'german': 'German',
        'math': 'Mathematics',
        'maths': 'Mathematics',
        'mathematics': 'Mathematics',
        'science': 'Science',
        'general science': 'Science',
        'physics': 'Physics',
        'chemistry': 'Chemistry',
        'biology': 'Biology',
        'botany': 'Biology',
        'zoology': 'Biology',
        'environmental science': 'Environmental Science',
        'evs': 'Environmental Science',
        'environmental studies': 'Environmental Science',
        'social science': 'Social Science',
        'sst': 'Social Science',
        'social studies': 'Social Science',
        'history': 'History',
        'geography': 'Geography',
        'political science': 'Political Science',
        'polity': 'Political Science',
        'politics': 'Political Science',
        'economics': 'Economics',
        'sociology': 'Sociology',
        'psychology': 'Psychology',
        'civics': 'Civics',
        'philosophy': 'Philosophy',
        'commerce': 'Commerce',
        'accountancy': 'Accountancy',
        'accounting': 'Accountancy',
        'accounts': 'Accountancy',
        'business studies': 'Business Studies',
        'business': 'Business Studies',
        'home science': 'Home Science / Family Studies',
        'family studies': 'Home Science / Family Studies',
        'legal studies': 'Legal Studies',
        'law': 'Legal Studies',
        'library science': 'Library Science',
        'computer': 'Computer Science',
        'computer science': 'Computer Science',
        'it': 'Computer Science',
        'information technology': 'Computer Science',
        'vocal music': 'Vocal Music Classical',
        'classical music': 'Vocal Music Classical',
        'instrumental music': 'Instrumental Music Classical',
        'western music': 'Vocal Music Western',
        'western vocal': 'Vocal Music Western',
        'guitar': 'Instrumental Music Western',
        'piano': 'Instrumental Music Western',
        'violin': 'Instrumental Music Western',
        'drum': 'Instrumental Music Western',
        'tabla': 'Instrumental Music Classical',
        'sitar': 'Instrumental Music Classical',
        'flute': 'Instrumental Music Classical',
        'graphics': 'Graphics',
        'photography': 'Photography',
        'photo': 'Photography',
        'ceramics': 'Ceramics',
        'pottery': 'Ceramics',
        'woodcraft': 'Woodcraft',
        'carpentry': 'Woodcraft',
        'sculpture': 'Sculptury',
        'sculptury': 'Sculptury',
        'classical dance': 'Dance (Classical)',
        'bharatanatyam': 'Dance (Classical)',
        'kathak': 'Dance (Classical)',
        'kuchipudi': 'Dance (Classical)',
        'odissi': 'Dance (Classical)',
        'western dance': 'Dance (Western)',
        'contemporary': 'Dance (Western)',
        'hip hop': 'Dance (Western)',
        'ballet': 'Dance (Western)',
        'dance': 'Dance (Western)',
        'art': 'Arts',
        'fine art': 'Arts',
        'painting': 'Arts',
        'drawing': 'Arts',
        'craft': 'Arts',
        'theatre': 'Theatre / Drama',
        'drama': 'Theatre / Drama',
        'acting': 'Theatre / Drama',
        'robotics': 'Robotics',
        'fashion': 'Fashion',
        'clothing': 'Fashion',
        'textile': 'Fashion',
        'film': 'Film Making',
        'film making': 'Film Making',
        'cinematography': 'Film Making',
        'animation': 'Animation',
        'debate': 'Debate & Public Speaking',
        'public speaking': 'Debate & Public Speaking',
        'elocution': 'Debate & Public Speaking',
        'creative writing': 'Creative Writing',
        'poetry': 'Creative Writing',
        'story writing': 'Creative Writing',
        'quiz': 'Quiz',
        'quizzing': 'Quiz',
        'physical education': 'General Sport Teacher',
        'pe': 'General Sport Teacher',
        'sports': 'General Sport Teacher',
        'athletics': 'Athletics',
        'track and field': 'Athletics',
        'yoga': 'Yoga',
        'cricket': 'Cricket',
        'badminton': 'Badminton',
        'tennis': 'Tennis',
        'basketball': 'Basketball',
        'football': 'Football',
        'soccer': 'Football',
        'hockey': 'Hockey',
        'equestrian': 'Equestrian',
        'horse riding': 'Equestrian',
        'squash': 'Squash',
        'chess': 'Chess',
        'volleyball': 'Volleyball',
        'swimming': 'Swimming',
        'golf': 'Golf',
        'table tennis': 'Table Tennis',
        'tt': 'Table Tennis',
        'ping pong': 'Table Tennis',
        'gymnastics': 'Gymnastics',
        'martial arts': 'Martial Arts',
        'karate': 'Martial Arts',
        'judo': 'Martial Arts',
        'taekwondo': 'Martial Arts',
        'shooting': 'Shooting',
        'skating': 'Skating',
        'boxing': 'Boxing',
        'ai': 'Artificial Intelligence',
        'artificial intelligence': 'Artificial Intelligence',
        'machine learning': 'Artificial Intelligence',
        'ml': 'Artificial Intelligence',
        'deep learning': 'Artificial Intelligence',
        'web': 'Web Development',
        'web development': 'Web Development',
        'web design': 'Web Development',
        'html': 'Web Development',
        'css': 'Web Development',
        'javascript': 'Web Development',
        'database': 'Database Management',
        'sql': 'Database Management',
        'dbms': 'Database Management',
        'network': 'Network Administration',
        'networking': 'Network Administration',
        'system': 'System Administration',
        'windows': 'System Administration',
        'linux': 'System Administration',
        'tech support': 'IT Support',
        'technical support': 'IT Support',
        'helpdesk': 'IT Support',
        'edtech': 'Educational Technology Integration',
        'educational technology': 'Educational Technology Integration',
        'smart class': 'Educational Technology Integration',
        'lms': 'Learning Management Systems (LMS) Administration',
        'learning management': 'Learning Management Systems (LMS) Administration',
        'moodle': 'Learning Management Systems (LMS) Administration',
        'canvas': 'Learning Management Systems (LMS) Administration',
        'digital content': 'Digital Content Creation',
        'e-content': 'Digital Content Creation',
        'online course': 'Digital Content Creation',
        'data analysis': 'Data Analysis',
        'analytics': 'Data Analysis',
        'excel': 'Data Analysis',
        'statistics': 'Data Analysis',
        'data science': 'Data Science',
        'big data': 'Data Science',
        'python': 'Data Science',
        'r programming': 'Data Science',
        'cybersecurity': 'Cybersecurity',
        'information security': 'Cybersecurity',
        'network security': 'Cybersecurity',
        'ethical hacking': 'Cybersecurity',
        'video editing': 'Video Editing',
        'premiere pro': 'Video Editing',
        'final cut': 'Video Editing',
        'graphic design': 'Graphic Design',
        'photoshop': 'Graphic Design',
        'illustrator': 'Graphic Design',
        'ms office': 'MS Office Suite Proficiency',
        'microsoft office': 'MS Office Suite Proficiency',
        'word': 'MS Office Suite Proficiency',
        'powerpoint': 'MS Office Suite Proficiency',
        'school administration': 'School Administration',
        'educational administration': 'School Administration',
        'office management': 'Office Management',
        'administrative management': 'Office Management',
        'event management': 'Event Management',
        'facilities management': 'Facilities Management',
        'inventory': 'Inventory Management',
        'stock management': 'Inventory Management',
        'front office management': 'Front Office Management',
        'reception management': 'Front Office Management',
        'communication': 'Communication Management',
        'public relations': 'Communication Management',
        'finance management': 'Finance',
        'financial management': 'Finance',
        'budgeting': 'Finance',
        'accounts management': 'Accounts Management',
        'bookkeeping': 'Accounts Management',
        'hr management': 'Human Resources (HR)',
        'human resource management': 'Human Resources (HR)',
        'personnel management': 'Human Resources (HR)',
        'marketing management': 'Marketing',
        'brand management': 'Marketing',
        'promotion': 'Marketing',
        'operations': 'Operations Management',
        'operations management': 'Operations Management',
        'transport': 'Transport Operations Management',
        'transport management': 'Transport Operations Management',
        'fleet management': 'Transport Operations Management',
        'hostel management': 'Hostel Management',
        'dormitory management': 'Hostel Management',
        'canteen management': 'Canteen Management',
        'food service management': 'Canteen Management',
        'security management': 'Security Management',
        'safety management': 'Security Management',
        'housekeeping management': 'Housekeeping Management',
        'cleaning management': 'Housekeeping Management',
        'maintenance management': 'Maintenance Management',
        'facility maintenance': 'Maintenance Management',
        'lab management': 'Laboratory Management',
        'laboratory management': 'Laboratory Management',
    }
    
    return role_mapping, level_mapping, skill_mapping

def best_match(input_term, master_list, threshold=70):
    """
    Find the best match for input_term in master_list using fuzzy matching
    Returns None if no match meets the threshold
    """
    if not input_term:
        return None
        
    # Clean the input term
    input_term = re.sub(r'[^\w\s]', ' ', input_term.lower().strip())
    input_term = re.sub(r'\s+', ' ', input_term)
    
    # Get the best match
    best_match = process.extractOne(input_term, master_list)
    
    if best_match and best_match[1] >= threshold:
        return best_match[0]
    return None

def extract_components(input_skill, role_mapping, level_mapping, skill_mapping, 
                       roles, levels, skills):
    """
    Extract skill, role, and level components from the input skill
    """
    input_skill = str(input_skill).strip()
    
    # Initialize result
    extracted = {
        'original': input_skill,
        'skill': None,
        'role': None,
        'level': None
    }
    
    # Convert to lowercase for matching
    input_lower = input_skill.lower()
    
    # Extract level from common prefixes/patterns
    level_indicators = {
        r'\bday\s*care\b': 'Day Care',
        r'\bpre[-\s]*(primary|school)\b': 'Pre-Primary',
        r'\b(nursery|kindergarten|kg|play\s*school|playgroup|montessori)\b': 'Pre-Primary',
        r'\bprt\b': 'Primary (PRT)',
        r'\bprimary\b': 'Primary (PRT)',
        r'\btgt\b': 'TGT (Trained Graduate Teacher)',
        r'\b(middle|secondary|high)\s*school\b': 'TGT (Trained Graduate Teacher)',
        r'\bpgt\b': 'PGT (Post Grad Teacher)',
        r'\b(senior|higher)\s*(secondary)\b': 'PGT (Post Grad Teacher)',
    }
    
    for pattern, level in level_indicators.items():
        if re.search(pattern, input_lower):
            extracted['level'] = level
            break
    
    # Clean input by removing role and level indicators for better skill matching
    cleaned_input = input_lower
    for prefix in ['prt', 'tgt', 'pgt', 'pre primary', 'pre-primary', 'primary', 'secondary']:
        cleaned_input = re.sub(r'\b' + prefix + r'\b', '', cleaned_input)
    
    # Try direct mapping first (for efficiency)
    for term, mapped_role in role_mapping.items():
        if term in input_lower:
            extracted['role'] = mapped_role
            cleaned_input = cleaned_input.replace(term, '')
            break
    
    for term, mapped_skill in skill_mapping.items():
        if term in input_lower:
            extracted['skill'] = mapped_skill
            cleaned_input = cleaned_input.replace(term, '')
            break
    
    # If direct mapping didn't yield results, try fuzzy matching
    if not extracted['role']:
        extracted['role'] = best_match(input_lower, roles)
    
    if not extracted['skill']:
        extracted['skill'] = best_match(cleaned_input, skills)
    
    if not extracted['level'] and extracted['role'] == 'Teacher':
        # For teachers without explicit level, use fuzzy matching
        extracted['level'] = best_match(input_lower, levels)
    elif not extracted['level'] and extracted['role'] != 'Teacher':
        # For non-teaching roles, set level to NA
        extracted['level'] = 'NA'
    
    # Special case handling
    if 'mother teacher' in input_lower:
        extracted['role'] = 'Mother Teacher'
        extracted['level'] = extracted['level'] or 'Pre-Primary'
    
    if 'assistant' in input_lower and 'teacher' in input_lower:
        extracted['role'] = 'Assistant Teacher'
    
    if 'coordinator' in input_lower and not any(term in input_lower for term in ['academic', 'event']):
        extracted['role'] = 'Academic Coordinator'
    
    if 'hod' in input_lower or ('head' in input_lower and 'department' in input_lower):
        extracted['role'] = 'Head of Department'
    
    # Final check - set defaults if still None
    if not extracted['skill'] and 'teacher' in input_lower:
        # Try to extract subject from the cleaned input
        words = cleaned_input.split()
        for word in words:
            if word in skill_mapping:
                extracted['skill'] = skill_mapping[word]
                break
    
    if not extracted['role']:
        if any(teaching_term in input_lower for teaching_term in ['teacher', 'faculty', 'lecturer', 'professor']):
            extracted['role'] = 'Teacher'
        else:
            extracted['role'] = 'Others'
    
    if not extracted['level'] and extracted['role'] == 'Teacher':
        extracted['level'] = 'Other'
    elif not extracted['level']:
        extracted['level'] = 'NA'
    
    return extracted

def process_excel(file_path, sheet_name):
    """
    Process Excel file and extract skill components
    """
    try:
        # Load data
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if 'Primary Skill' not in df.columns:
            raise ValueError("Column 'Primary Skill' not found in the Excel sheet")
        
        # Initialize master lists and mappings
        roles, levels, skills = initialize_master_lists()
        role_mapping, level_mapping, skill_mapping = create_mapping_dictionaries()
        
        # Prepare a partial function that only needs the input skill.
        worker = partial(
            extract_components,
            role_mapping=role_mapping,
            level_mapping=level_mapping,
            skill_mapping=skill_mapping,
            roles=roles,
            levels=levels,
            skills=skills
        )
        
        # Filter out rows with missing 'Primary Skill'
        input_skills = df['Primary Skill'].dropna().tolist()
        
        # Process each skill concurrently using a process pool.
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # executor.map returns results in order corresponding to input_skills
            results = list(executor.map(worker, input_skills))
        
        # Create a DataFrame from the extracted results.
        result_df = pd.DataFrame(results)
        
        # Merge the results back into the original DataFrame.
        # (Assuming the order of non-NA 'Primary Skill' rows matches the results order)
        idx = df['Primary Skill'].notna()
        for col in ['skill', 'role', 'level']:
            df.loc[idx, col.capitalize()] = result_df[col].values
        # Process each skill
        # results = []
        # for idx, row in df.iterrows():
        #     if pd.isna(row['Primary Skill']):
        #         continue
                
        #     extracted = extract_components(
        #         row['Primary Skill'], 
        #         role_mapping, 
        #         level_mapping, 
        #         skill_mapping,
        #         roles, 
        #         levels, 
        #         skills
        #     )
            
        #     results.append(extracted)
        
        # # Convert to DataFrame
        # result_df = pd.DataFrame(results)
        
        # # Add to original DataFrame
        # for col in ['skill', 'role', 'level']:
        #     df[col.capitalize()] = result_df[col]
        
        # return df, result_df
    
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return None, None

def analyze_results(result_df):
    """
    Analyze the results of skill extraction
    """
    if result_df is None or len(result_df) == 0:
        return None
    
    analysis = {
        'total_entries': len(result_df),
        'entries_with_skill': result_df['skill'].notnull().sum(),
        'entries_with_role': result_df['role'].notnull().sum(),
        'entries_with_level': result_df['level'].notnull().sum(),
        'top_skills': result_df['skill'].value_counts().head(10).to_dict(),
        'top_roles': result_df['role'].value_counts().head(10).to_dict(),
        'top_levels': result_df['level'].value_counts().head(5).to_dict(),
        'skill_role_combinations': result_df.groupby(['skill', 'role']).size().sort_values(ascending=False).head(10).to_dict()
    }
    
    return analysis

def save_results(df, file_path, sheet_name):
    """
    Save processed results to a new Excel file
    """
    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Add a mapping sheet
            roles, levels, skills = initialize_master_lists()
            mapping_df = pd.DataFrame({
                'Roles': roles + [None] * (max(len(skills), len(levels)) - len(roles)),
                'Levels': levels + [None] * (max(len(skills), len(roles)) - len(levels)),
                'Primary Skill': skills + [None] * (max(len(roles), len(levels)) - len(skills))
            })
            mapping_df.to_excel(writer, sheet_name='Master_Lists', index=False)
            
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False

def main():
    """
    Main function to process the Excel file
    """
    file_path = "data/Candidates.xlsx"
    sheet_name = "Sheet1"
    output_file = "data/Candidates.xlsx"
    output_sheet = "Processed_Skills"
    
    print(f"Processing {file_path}, sheet: {sheet_name}...")
    
    # Process Excel file
    df, result_df = process_excel(file_path, sheet_name)
    
    if df is None:
        print("Processing failed. Check the error message above.")
        return
    
    # Analyze results
    analysis = analyze_results(result_df)
    
    if analysis:
        print("\nAnalysis Results:")
        print(f"Total entries processed: {analysis['total_entries']}")
        print(f"Entries with identified skill: {analysis['entries_with_skill']} ({analysis['entries_with_skill']/analysis['total_entries']*100:.1f}%)")
        print(f"Entries with identified role: {analysis['entries_with_role']} ({analysis['entries_with_role']/analysis['total_entries']*100:.1f}%)")
        print(f"Entries with identified level: {analysis['entries_with_level']} ({analysis['entries_with_level']/analysis['total_entries']*100:.1f}%)")
        
        print("\nTop 5 Skills:")
        for skill, count in list(analysis['top_skills'].items())[:5]:
            print(f"  - {skill}: {count}")
            
        print("\nTop 5 Roles:")
        for role, count in list(analysis['top_roles'].items())[:5]:
            print(f"  - {role}: {count}")
    
    # Save results
    if save_results(df, output_file, output_sheet):
        print(f"\nResults saved to {output_file}, sheet: {output_sheet}")
    else:
        print("\nFailed to save results.")
        