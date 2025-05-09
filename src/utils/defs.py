# Define master lists
ROLES = [
    "Teacher", "Mother Teacher", "Assistant Teacher",
    "Academic Coordinator", "Head of Department", "Vice Principal", "Headmistress", 
    "Principal", "Director", "Events Coordinator", "School Counselor", 
    "Admissions Counselor", "School Nurse", "School Doctor", "Sport Coach",
    "Librarian", "Lab Assistant", "Lab Technician", "Front Desk Executive", 
    "Clerk", "Office Assistant", "HR Executive", "Finance Executive", 
    "Facilities Manager", "Admin Officer", "Marketing Executive", "Content Writer",
    "Graphic Designer", "IT Support Staff", "System Admin", "Software Developer", 
    "Analyst", "Canteen Staff", "Warden", "Groundsman", "Guard", "Peon", 
    "Bus Driver", "Housekeeping Staff", "Maintenance Staff", "Others"
]

LEVELS = [
    "Day Care", "Pre-Primary", "PRT", "TGT", "PGT", "NA", "Other"
]

SKILLS = [
    # Languages
    "English", "Hindi", "Sanskrit", "French", "Spanish", "Japanese", "German",
    # Core Subjects
    "Mathematics", "Science", "Physics", "Chemistry", "Biology", 
    "Environmental Science", "Social Science", "History", "Geography", 
    "Political Science", "Economics", "Sociology", "Psychology", "Civics", 
    "Philosophy", "Commerce", "Accountancy", "Business Studies", 
    "Home Science", "Family Studies", "Legal Studies", "Library Science", 
    "Computer Science",
    # Arts & Performance
    "Vocal Music Classical", "Instrumental Music Classical", 
    "Vocal Music Western", "Instrumental Music Western", "Graphics", 
    "Photography", "Ceramics", "Woodcraft", "Sculptury", "Dance (Classical)", 
    "Dance (Western)", "Arts", "Theatre", "Drama", "Robotics", "Fashion", 
    "Film Making", "Animation", "Debate & Public Speaking", "Creative Writing", "Quiz",
    # Sports
    "General Sport", "Athletics", "Yoga", "Cricket", "Badminton", "Tennis", 
    "Basketball", "Football", "Hockey", "Equestrian", "Squash", "Chess", 
    "Volleyball", "Swimming", "Golf", "Table Tennis", "Gymnastics", 
    "Martial Arts", "Shooting", "Skating", "Boxing",
    # Technology
    "Artificial Intelligence", "Web Development", "Database Management", 
    "Network Administration", "System Administration", "IT Support", 
    "Educational Technology Integration", "Learning Management Systems", 
    "Digital Content Creation", "Data Analysis", "Data Science", "Cybersecurity", 
    "Video Editing", "Graphic Design", "MS Office Suite",
    # Administrative
    "School Administration", "Office Management", "Event Management", 
    "Facilities Management", "Inventory Management", "Front Office Management", 
    "Communication Management", "Finance", "Accounts Management", 
    "Human Resources", "Marketing", "Operations Management", 
    "Transport Operations Management", "Hostel Management", "Canteen Management", 
    "Security Management", "Housekeeping Management", "Maintenance Management", 
    "Laboratory Management"
    "Health Care& Well Being", 
]

# Create mapping dictionaries for standardization
ROLE_MAPPING = {
    # Teaching roles
    r'\b(teacher|faculty|educator|trainer|instructor|tutor)\b': 'Teacher',
    r'\bmother\s*teacher\b': 'Mother Teacher',
    r'\b(assistant|support|co|junior)\s*teacher\b': 'Assistant Teacher',
    
    # Administrative roles
    r'\b(academic|curriculum)\s*(coordinator|cord|cordinator)\b': 'Academic Coordinator',
    r'\b(hod|head|head\s*of\s*department)\b': 'Head of Department',
    r'\bvice\s*principal\b': 'Vice Principal',
    r'\bheadmistress\b': 'Headmistress',
    r'\bprincipal\b': 'Principal',
    r'\bdirector\b': 'Director',
    r'\bevent\s*(coordinator|manager)\b': 'Events Coordinator',
    r'\b(school|educational)\s*counselo?r\b': 'School Counselor',
    r'\badmission\s*(counselo?r|manager|coordinator|officer)\b': 'Admissions Counselor',
    r'\b(school|staff)\s*nurse\b': 'School Nurse',
    r'\b(school|staff)\s*doctor\b': 'School Doctor',
    r'\b(sport|game|athletic)\s*(coach|trainer)\b': 'Sport Coach',
    r'\blibrarian\b': 'Librarian',
    r'\blab\s*(assistant|technician|incharge)\b': 'Lab Assistant',
    
    # Support staff
    r'\bfront\s*(desk|office)\b': 'Front Desk Executive',
    r'\b(clerk|office\s*assistant)\b': 'Clerk',
    r'\bhr\s*(executive|manager|associate)\b': 'HR Executive',
    r'\b(finance|account|accountant)\s*(executive|manager)\b': 'Finance Executive',
    r'\bfacilities\s*manager\b': 'Facilities Manager',
    r'\badmin(\s*officer)?\b': 'Admin Officer',
    r'\bmarketing\s*(executive|manager)\b': 'Marketing Executive',
    r'\bcontent\s*writer\b': 'Content Writer',
    r'\bgraphic\s*designer\b': 'Graphic Designer',
    r'\bit\s*support\b': 'IT Support Staff',
    r'\bsystem\s*admin\b': 'System Admin',
    r'\bsoftware\s*developer\b': 'Software Developer',
    r'\banalyst\b': 'Analyst',
    
    # Non-teaching staff
    r'\bcanteen\s*staff\b': 'Canteen Staff',
    r'\bwarden\b': 'Warden',
    r'\bgroundsman\b': 'Groundsman',
    r'\bguard\b': 'Guard',
    r'\bpeon\b': 'Peon',
    r'\bdriver\b': 'Bus Driver',
    r'\bhousekeeping\b': 'Housekeeping Staff',
    r'\bmaintenance\b': 'Maintenance Staff'
}

LEVEL_MAPPING = {
    r'\bday\s*care\b': 'Day Care',
    r'\b(pre\s*primary|nursery|kindergarten|kg|pre\s*school|montessori|playgroup)\b': 'Pre-Primary',
    r'\b(prt|primary)\b': 'PRT',
    r'\btgt\b': 'TGT',
    r'\bpgt\b': 'PGT',
}

# Comprehensive mapping of skills by category
SKILL_MAPPING = {
    # Languages
    r'\benglish\b': 'English',
    r'\bhindi\b': 'Hindi',
    r'\bsanskrit\b': 'Sanskrit',
    r'\bfrench\b': 'French',
    r'\bspanish\b': 'Spanish',
    r'\bjap(a|e)nese\b': 'Japanese',
    r'\bgerman\b': 'German',
    
    # STEM Subjects
    r'\bmath(ematics|s)?\b': 'Mathematics',
    r'\b(general\s*)?science\b': 'Science',
    r'\bphysics\b': 'Physics',
    r'\bchemistry\b': 'Chemistry',
    r'\bbiology\b': 'Biology',
    r'\b(environmental|evs)\s*(science|studies)\b': 'Environmental Science',
    r'\b(social\s*science|sst)\b': 'Social Science',
    r'\bhistory\b': 'History',
    r'\bgeography\b': 'Geography',
    r'\bpolitical\s*science\b': 'Political Science',
    r'\beconomics\b': 'Economics',
    r'\bsociology\b': 'Sociology',
    r'\bpsychology\b': 'Psychology',
    r'\bcivics\b': 'Civics',
    r'\bphilosophy\b': 'Philosophy',
    r'\bcommerce\b': 'Commerce',
    r'\baccountancy\b': 'Accountancy',
    r'\bbusiness\s*studies\b': 'Business Studies',
    r'\bhome\s*science\b': 'Home Science',
    r'\blegal\s*studies\b': 'Legal Studies',
    r'\blibrary\s*science\b': 'Library Science',
    r'\bcomputer\s*(science)?\b': 'Computer Science',
    
    # Arts and Performance
    r'\b(vocal|classical)\s*music\b': 'Vocal Music Classical',
    r'\binstrumental\s*(music)?\s*classical\b': 'Instrumental Music Classical',
    r'\bwestern\s*music\b': 'Vocal Music Western',
    r'\b(piano|guitar)\s*teacher\b': 'Instrumental Music Western',
    r'\bgraphics\b': 'Graphics',
    r'\bphotography\b': 'Photography',
    r'\bceramics\b': 'Ceramics',
    r'\bwoodcraft\b': 'Woodcraft',
    r'\bsculptur(e|y)\b': 'Sculptury',
    r'\b(classical|indian)\s*dance\b': 'Dance (Classical)',
    r'\bwestern\s*dance\b': 'Dance (Western)',
    r'\b(art|fine\s*art|drawing|painting)\b': 'Arts',
    r'\b(theatre|drama)\b': 'Theatre',
    r'\brobotics\b': 'Robotics',
    r'\bfashion\b': 'Fashion',
    r'\bfilm\s*making\b': 'Film Making',
    r'\banimation\b': 'Animation',
    r'\bdebate\b': 'Debate & Public Speaking',
    r'\bcreative\s*writing\b': 'Creative Writing',
    r'\bquiz\b': 'Quiz',
    
    # Sports
    r'\b(physical\s*education|sports?\s*teacher|pt|ped)\b': 'General Sport',
    r'\bathletics\b': 'Athletics',
    r'\byoga\b': 'Yoga',
    r'\bcricket\b': 'Cricket',
    r'\bbadminton\b': 'Badminton',
    r'\btennis\b': 'Tennis',
    r'\bbasketball\b': 'Basketball',
    r'\bfootball\b': 'Football',
    r'\bhockey\b': 'Hockey',
    r'\bequestrian\b': 'Equestrian',
    r'\bsquash\b': 'Squash',
    r'\bchess\b': 'Chess',
    r'\bvolleyball\b': 'Volleyball',
    r'\bswimming\b': 'Swimming',
    r'\bgolf\b': 'Golf',
    r'\btable\s*tennis\b': 'Table Tennis',
    r'\bgymnastics\b': 'Gymnastics',
    r'\b(martial\s*arts|karate)\b': 'Martial Arts',
    r'\bshooting\b': 'Shooting',
    r'\bskating\b': 'Skating',
    r'\bboxing\b': 'Boxing',
    
    # Technology
    r'\bartificial\s*intelligence\b': 'Artificial Intelligence',
    r'\bweb\s*development\b': 'Web Development',
    r'\bdatabase\b': 'Database Management',
    r'\bnetwork\b': 'Network Administration',
    r'\bsystem\s*admin\b': 'System Administration',
    r'\bit\s*support\b': 'IT Support',
    r'\beducational\s*technology\b': 'Educational Technology Integration',
    r'\blms\b': 'Learning Management Systems',
    r'\bdigital\s*content\b': 'Digital Content Creation',
    r'\bdata\s*analysis\b': 'Data Analysis',
    r'\bdata\s*science\b': 'Data Science',
    r'\bcybersecurity\b': 'Cybersecurity',
    r'\bvideo\s*editing\b': 'Video Editing',
    r'\bgraphic\s*design\b': 'Graphic Design',
    r'\bms\s*office\b': 'MS Office Suite',
    
    # Administrative
    r'\bschool\s*admin\b': 'School Administration',
    r'\boffice\s*manage\b': 'Office Management',
    r'\bevent\s*manage\b': 'Event Management',
    r'\bfacilities\b': 'Facilities Management',
    r'\binventory\b': 'Inventory Management',
    r'\bfront\s*office\b': 'Front Office Management',
    r'\bcommunication\b': 'Communication Management',
    r'\bfinance\b': 'Finance',
    r'\baccounts?\s*manage\b': 'Accounts Management',
    r'\bhuman\s*resources\b': 'Human Resources',
    r'\bmarketing\b': 'Marketing',
    r'\boperations\b': 'Operations Management',
    r'\btransport\b': 'Transport Operations Management',
    r'\bhostel\b': 'Hostel Management',
    r'\bcanteen\b': 'Canteen Management',
    r'\bsecurity\b': 'Security Management',
    r'\bhousekeeping\b': 'Housekeeping Management',
    r'\bmaintenance\b': 'Maintenance Management',
    r'\blaboratory\s*manage\b': 'Laboratory Management',
}
import pandas as pd
from db import engine

CITIES = pd.read_sql_query('SELECT c."Id", c."Name" as "name", s."Name" as "state" FROM "City" c JOIN "State" s ON s."Id"=c."StateId"', engine).set_index("Id")
