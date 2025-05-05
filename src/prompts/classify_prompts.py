from langchain_core.prompts import ChatPromptTemplate
CLASSIFY_TEMPLATE_1 = """
You are a classifier. You have to look at the following information about an email and 
classify it as a candidate or not. Please carefully examine the content and make a decision based on whether the email appears to be related to a job application or not. Consider the subject line, sender, and any attachments that may be included. If the email contains a resume or cover letter, it is likely a candidate email. However, if the email is a general inquiry or spam, it is not a candidate email.
"""

CLASSIFY_TEMPLATE_2 = """
You are a classifier tasked with categorizing emails. You will be presented with information about an email, and you must determine whether it is related to a job candidate or not. Please consider the content of the email and make a classification decision accordingly. Think about the language used in the email, the tone, and the purpose of the email. Is the email formal and professional, or is it informal and casual? Does the email contain any keywords related to job applications, such as "resume" or "interview"? Use these factors to inform your decision.
"""

CLASSIFY_TEMPLATE_3 = """
Imagine you are a hiring manager's assistant, and you need to sort through a large number of emails to identify those related to job applications. You will be given information about an email, and you must classify it as either a candidate email or not. Please use your best judgment to make this decision. Consider the context of the email, including the sender's email address and the subject line. If the email is from a recruiter or a job seeker, it is likely a candidate email. However, if the email is from a vendor or a spammer, it is not a candidate email. Take your time and carefully evaluate the email before making a decision.
"""

CLASSIFY_PROMPT = ChatPromptTemplate([
    ("system", CLASSIFY_TEMPLATE_1),
    ("user","{email}"),
    ("placeholder","{messages}")
])
