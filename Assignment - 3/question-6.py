import pymongo
import urllib.request
from bs4 import BeautifulSoup

# Connect to MongoDB
mongo_connection = pymongo.MongoClient("mongodb://localhost:27017/")
database_instance = mongo_connection["Assignmentcrawlerdb"]
pages_data_collection = database_instance["pages"]
faculty_data_collection = database_instance["professors"]

# Define utility functions first
def fetch_label_value(label_tag):
    key = label_tag.get_text(strip=True).lower().rstrip(':')
    sibling = label_tag.next_sibling
    while sibling and (isinstance(sibling, str) and sibling.strip() in ['', ':'] or sibling.name == 'br'):
        sibling = sibling.next_sibling
    value_parts = []
    while sibling and not (hasattr(sibling, 'name') and sibling.name == 'strong'):
        if isinstance(sibling, str):
            content = sibling.strip()
            if content and content != ':':
                value_parts.append(content)
        elif sibling.name == 'a':
            if key == 'email':
                value_parts.append(sibling.get_text(strip=True))
            elif key == 'web':
                value_parts.append(sibling.get('href', '').strip())
            else:
                value_parts.append(sibling.get_text(strip=True))
        elif sibling.name == 'br':
            pass  # Skip line breaks
        else:
            value_parts.append(sibling.get_text(strip=True))
        sibling = sibling.next_sibling
    return key, ' '.join(value_parts).strip()


# Ensure the unique index on 'email' exists
faculty_data_collection.create_index('email', unique=True)
print("Ensured unique index on 'email'.")

# Always download the page to get the latest content
faculty_url = 'https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml'
print("Downloading the Permanent Faculty page...")

try:
    faculty_response = urllib.request.urlopen(faculty_url)
    faculty_html = faculty_response.read().decode('utf-8')
except Exception as download_error:
    print(f"Failed to retrieve the page: {download_error}")
    exit(1)

# Parse the HTML data
parsed_html = BeautifulSoup(faculty_html, 'html.parser')

# Find the faculty section
faculty_html_section = parsed_html.find('section', class_='text-images')
if not faculty_html_section:
    print("Faculty section not found. Please check the HTML structure.")
    exit(1)

faculty_profile_tags = faculty_html_section.find_all('h2')
if not faculty_profile_tags:
    print("No faculty profiles found. Please check the HTML structure.")
    exit(1)

print(f"Found {len(faculty_profile_tags)} faculty profiles.")

# Process faculty profiles
unique_emails = set()

for profile_tag in faculty_profile_tags:
    professor_name = profile_tag.get_text(strip=True)

    # Initialize details
    professor_title = None
    professor_office = None
    professor_phone = None
    professor_email = None
    professor_website = None

    # Get details from the <p> tag following the <h2>
    profile_details = profile_tag.find_next_sibling('p')

    if profile_details:
        all_label_tags = profile_details.find_all('strong')
        for label in all_label_tags:
            key, value = fetch_label_value(label)
            if key == 'title':
                professor_title = value
            elif key == 'office':
                professor_office = value
            elif key == 'phone':
                professor_phone = value
            elif key == 'email':
                professor_email = value
            elif key == 'web':
                professor_website = value

    # Skip if critical data is missing
    if not professor_name or not professor_email:
        print(f"Missing critical information for a faculty member ({professor_name}). Skipping.")
        continue

    if professor_email in unique_emails:
        print(f"Duplicate email found in HTML for {professor_name} ({professor_email}). Skipping duplicate.")
        continue
    unique_emails.add(professor_email)

    # Prepare professor data for insertion
    professor_record = {
        'name': professor_name,
        'title': professor_title,
        'office': professor_office,
        'phone': professor_phone,
        'email': professor_email,
        'website': professor_website
    }

    # Insert into MongoDB
    try:
        faculty_data_collection.insert_one(professor_record)
        print(f"Inserted professor: {professor_name}")
        print(f"Name: {professor_name}")
        print(f"Title: {professor_title}")
        print(f"Office: {professor_office}")
        print(f"Phone: {professor_phone}")
        print(f"Email: {professor_email}")
        print(f"Website: {professor_website}")
        print("---")
    except pymongo.errors.DuplicateKeyError:
        print(f"Professor with email {professor_email} already exists in MongoDB. Skipping.")

# Final summary
print(f"Total unique professors inserted: {len(unique_emails)}")
