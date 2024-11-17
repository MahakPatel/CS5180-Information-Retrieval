import urllib.request
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pymongo

# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
database = mongo_client["Assignmentcrawlerdb"]
html_pages_collection = database["pages"]


class URLFrontier:
    def __init__(self):
        self.queue = []
        self.processed = set()
        self.is_done = False

    def add_url(self, url):
        if url not in self.processed and url not in self.queue:
            self.queue.append(url)

    def get_next_url(self):
        if self.queue:
            url = self.queue.pop(0)
            self.processed.add(url)
            return url
        else:
            return None

    def is_finished(self):
        return self.is_done or not self.queue

    def mark_as_done(self):
        self.queue = []
        self.is_done = True


def fetch_html_content(url):
    try:
        response = urllib.request.urlopen(url)
        content_type = response.headers.get('Content-Type')
        if 'text/html' in content_type:
            html_data = response.read()
            return html_data
        else:
            return None
    except Exception as error:
        print(f"Failed to fetch {url}: {error}")
        return None


def save_page_to_db(url, html):
    html_pages_collection.insert_one({'url': url, 'html': html.decode('utf-8')})


def extract_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    extracted_urls = []
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        # Build absolute URL
        absolute_url = urljoin(base_url, href)
        # Only consider HTTP and HTTPS URLs
        parsed_url = urlparse(absolute_url)
        if parsed_url.scheme in ['http', 'https']:
            # Only considering the HTML and SHTML pages
            path = parsed_url.path
            if path.endswith('.html') or path.endswith('.shtml') or path.endswith('.htm') or path == '' or path.endswith('/'):
                # Only considering the URLs within the CS website
                if absolute_url.startswith('https://www.cpp.edu/sci/computer-science/'):
                    extracted_urls.append(absolute_url)
    return extracted_urls


def is_target_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.find('h1', class_='cpp-h1')
    if heading and heading.text.strip() == 'Permanent Faculty':
        return True
    return False


def report_target_page(url):
    print(f"Target page found: {url}")


def crawl_frontier(frontier):
    while not frontier.is_finished():
        current_url = frontier.get_next_url()
        if current_url is None:
            break
        print(f"Visiting: {current_url}")
        html_content = fetch_html_content(current_url)
        if html_content:
            save_page_to_db(current_url, html_content)
            if is_target_page(html_content):
                report_target_page(current_url)
                frontier.mark_as_done()
            else:
                linked_urls = extract_links(html_content, current_url)
                for link in linked_urls:
                    if link not in frontier.processed:
                        frontier.add_url(link)


if __name__ == "__main__":
    initial_url = 'https://www.cpp.edu/sci/computer-science/'
    url_frontier = URLFrontier()
    url_frontier.add_url(initial_url)
    crawl_frontier(url_frontier)
