# install selenium, chromedriver, bs4 in advance
# can use IPython for test

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import json

# Initialize Selenium
chrome_driver_path = "/opt/homebrew/Caskroom/chromedriver/..."  # replace it with your own chromedriver absolute path
driver = webdriver.Chrome(service=Service(chrome_driver_path))

# Open the course offering page, will jump to gluegent login page by itself
driver.get('https://campus.icu.ac.jp/icumap/ehb/SearchCO.aspx') # path effective on Aug 7, 2024

# Enter username and password
try:
    username = driver.find_element(By.NAME, 'username')
    password = driver.find_element(By.NAME, 'password')
    print("Login page loaded successfully")
except NoSuchElementException:
    print("Failed to load login page")
    driver.quit()
    exit()

# remember to replace these with your own effective icu acount
username.send_keys('your icu id')  
password.send_keys('your password')

# Click the login button
login_button = driver.find_element(By.ID, 'login_button')
login_button.click()

# Wait for the page to load completely
time.sleep(1)  # Adjust the wait time as needed

# Click the "Search" button
search_button = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_btn_search')
search_button.click()

# Wait for the search results to load completely
time.sleep(1)  # Adjust the wait time as needed

# Define a function to extract course information from the current page
def extract_courses(page_soup):
    courses = []
    table = page_soup.find('table', {'id': 'ctl00_ContentPlaceHolder1_grv_course'})
    if table:
        rows = table.find_all('tr')
        skip_next_tr = False # flag for the recognization of the page number tr lines (2 tr lines for icu course offering webpage case)
        for row in rows:
            if row.get('align') == 'center':  # the first line has align = 'center' while all of other wanted tr lines do not.
                skip_next_tr = True
                continue
            elif skip_next_tr: # The second line is in the table nested under the first line. No align label recognizable, so used "skip_next_tr" flag instead.
                skip_next_tr = False
                continue
            else:
                cols = row.find_all('td')  # bs4.element.ResultSet
                if cols:  # Only process if there are td elements (the format of the title row of the sybllubus consists <th>s for the content intead of <tr>s)
                    course = [col.text.strip() for col in cols if col.text.strip()]  # Extract and clean text
                    print(course)
                    courses.append(course)
    return courses

# Create a list to save all course information
all_courses = []

# Function to get and click the next page button
def click_next_page(current_page):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagination_row = soup.find('table', {'id': 'ctl00_ContentPlaceHolder1_grv_course'}).find_all('tr')[0]  # Find the row containing page numbers
    if not pagination_row:
        print("Pagination row not found")
        return False

    page_links = pagination_row.find_all('a')
    for link in page_links:
        if link.text.strip().isdigit():
            page_number = int(link.text.strip())
            if page_number == current_page + 1:
                next_page_button = driver.find_element(By.LINK_TEXT, str(page_number))
                next_page_button.click()
                return True
    return False

# Extract course information from the first page
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
all_courses.extend(extract_courses(soup))

# Initialize the current page number
current_page = 1

# Loop to click the "next page" button and scrape data from all pages
while True:
    if click_next_page(current_page) 
        time.sleep(2)  # Adjust the wait time as needed
        current_page += 1

        # Extract course information from the current page
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        page_courses = extract_courses(soup)
        print(page_courses)
        all_courses.extend(page_courses)
    else:
        print("All pages processed")
        break

# Save all course information to a local JSON file (will use SQLite instead for icucatalogue's following data filtering work)
with open('test.json', 'w', encoding='utf-8') as f:
    json.dump(all_courses, f, ensure_ascii=False, indent=4)

# Close the browser
driver.quit()
