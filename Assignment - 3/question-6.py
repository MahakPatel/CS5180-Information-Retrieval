import pymongo
import urllib.request
from bs4 import BeautifulSoup

# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["Assignmentcrawlerdb"]
html_pages_collection = mongo_db["pages"]
faculty_collection = mongo_db["professors"]

# Ensure the unique index on 'email' exists
faculty_collection.create_index('email', unique=True)
print("Ensured unique index on 'email'.")

# Target URL
faculty_page_url = 'https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml'

# Always download the page to get the latest content
print("Downloading the Permanent Faculty page...")
try:
    faculty_page_response = urllib.request.urlopen(faculty_page_url)
    faculty_html_data = faculty_page_response.read().decode('utf-8')
except Exception as fetch_error:
    print(f"Failed to retrieve the page: {fetch_error}")
    exit(1)

# Parse the HTML data
faculty_soup = BeautifulSoup(faculty_html_data, 'html.parser')

# Find the section containing the faculty members
faculty_section = faculty_soup.find('section', class_='text-images')

if not faculty_section:
    print("Faculty section not found. Please check the HTML structure.")
    exit(1)

# Find all <h2> tags within the faculty section
faculty_name_tags = faculty_section.find_all('h2')

print(f"Found {len(faculty_name_tags)} faculty profiles.")

if not faculty_name_tags:
    print("No faculty profiles found. Please check the HTML structure.")
    exit(1)


def parse_label_value(label_tag):
    label_key = label_tag.get_text(strip=True).lower().rstrip(':')
    sibling_node = label_tag.next_sibling
    while sibling_node and (isinstance(sibling_node, str) and sibling_node.strip() in ['', ':'] or sibling_node.name == 'br'):
        sibling_node = sibling_node.next_sibling
    label_value_parts = []
    while sibling_node and not (hasattr(sibling_node, 'name') and sibling_node.name == 'strong'):
        if isinstance(sibling_node, str):
            text_content = sibling_node.strip()
            if text_content and text_content != ':':
                label_value_parts.append(text_content)
        elif sibling_node.name == 'a':
            if label_key == 'email':
                label_value_parts.append(sibling_node.get_text(strip=True))
            elif label_key == 'web':
                label_value_parts.append(sibling_node.get('href', '').strip())
            else:
                label_value_parts.append(sibling_node.get_text(strip=True))
        elif sibling_node.name == 'br':
            pass  # Skip line breaks
        else:
            label_value_parts.append(sibling_node.get_text(strip=True))
        sibling_node = sibling_node.next_sibling
    label_value = ' '.join(label_value_parts).strip()
    return label_key, label_value


parsed_emails = set()

for faculty_name_tag in faculty_name_tags:
    faculty_name = faculty_name_tag.get_text(strip=True)

    # Initialize variables
    faculty_title = faculty_office = faculty_phone = faculty_email = faculty_website = None

    # The details are in the following <p> tag
    faculty_details_tag = faculty_name_tag.find_next_sibling('p')

    if faculty_details_tag:
        strong_tags_in_details = faculty_details_tag.find_all('strong')
        for strong_label_tag in strong_tags_in_details:
            field_key, field_value = parse_label_value(strong_label_tag)
            if field_key == 'title':
                faculty_title = field_value
            elif field_key == 'office':
                faculty_office = field_value
            elif field_key == 'phone':
                faculty_phone = field_value
            elif field_key == 'email':
                faculty_email = field_value
            elif field_key == 'web':
                faculty_website = field_value

    if not faculty_name or not faculty_email:
        print(f"Missing critical information for a faculty member ({faculty_name}). Skipping.")
        continue

    if faculty_email in parsed_emails:
        print(f"Duplicate email found in HTML for {faculty_name} ({faculty_email}). Skipping duplicate.")
        continue
    parsed_emails.add(faculty_email)

    # Create a dictionary with the data
    faculty_data = {
        'name': faculty_name,
        'title': faculty_title,
        'office': faculty_office,
        'phone': faculty_phone,
        'email': faculty_email,
        'website': faculty_website
    }

    # Insert into MongoDB with error handling for duplicates
    try:
        faculty_collection.insert_one(faculty_data)
        print(f"Inserted professor: {faculty_name}")
        # Optional: Print extracted data for verification
        print(f"Name: {faculty_name}")
        print(f"Title: {faculty_title}")
        print(f"Office: {faculty_office}")
        print(f"Phone: {faculty_phone}")
        print(f"Email: {faculty_email}")
        print(f"Website: {faculty_website}")
        print("---")
    except pymongo.errors.DuplicateKeyError:
        print(f"Professor with email {faculty_email} already exists in MongoDB. Skipping.")

# Optional: Print the total number of unique professors inserted
print(f"Total unique professors inserted: {len(parsed_emails)}")
