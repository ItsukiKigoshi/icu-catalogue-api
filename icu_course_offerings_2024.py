# pip selenium
# pip bs4
# pip chromedriver_autoinstaller

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import sqlite3
import chromedriver_autoinstaller

# initialize Selenium
chromedriver_autoinstaller.install()
driver = webdriver.Chrome()

# open login page
driver.get('https://campus.icu.ac.jp/icumap/ehb/SearchCO.aspx')

# enter username and password
try:
    username = driver.find_element(By.NAME, 'username')
    password = driver.find_element(By.NAME, 'password')
    print("successfully loaded login page")
except NoSuchElementException:
    print("failed to load login page")
    driver.quit()
    exit()

username.send_keys('c271530i')
password.send_keys('BilBao0508')

# click "login"
login_button = driver.find_element(By.ID, 'login_button')
login_button.click()
time.sleep(1)

# click “Search"
search_button = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_btn_search')
search_button.click()
time.sleep(1)

def extract_courses(page_soup):
    courses = []
    table = page_soup.find('table', {'id': 'ctl00_ContentPlaceHolder1_grv_course'})
    if table:
        rows = table.find_all('tr')
        skip_next_tr = False
        for row in rows:
            if row.get('align') == 'center':
                skip_next_tr = True
                continue
            elif skip_next_tr:
                skip_next_tr = False
                continue
            else:
                cols = row.find_all('td')  # bs4.element.ResultSet
                if cols:  # skip empty cols
                    # status: deleted:0, normal:1, added
                    status = 0 if any(col.find('div', {'class': 'word_line_through'}) for col in cols) else 1
                    course_info = [col.text.strip() for col in cols]  # list
                    first_term = course_info[0].split('\n')
                    name_term = course_info[4].split('\n')
                    if len(name_term) == 3:
                        period = name_term[2]
                        room = "NULL"
                    elif len(name_term) == 4:
                        period = name_term[2]
                        room = name_term[3]
                    else:
                        period = "NULL"
                        room = "NULL"
                    registration_no = first_term[0]
                    term = first_term[1]
                    academic_year = first_term [2]
                    course_no = course_info[1]
                    major = course_info[1][:3]
                    level = course_info[1][3:4]  # 何番台 #added
                    language = course_info[2]
                    name_j = name_term[1]
                    name_e = name_term[0]
                    instructor = course_info[6]
                    credit_text = course_info[7]

                    # Extract number from (credit_text)
                    if len(credit_text) == 1:
                        credit = credit_text
                    elif credit_text[0] == "1":  # when credit == 1/3, data type stored in db is text
                        credit = credit_text
                    elif credit_text[0] == "3": # 卒論研究3/(9)
                        credit = credit_text[0]
                    else:
                        credit = credit_text[1]

                    courses.append((status, registration_no, term, academic_year, course_no, major, level, language,
                                        name_j, name_e, period, room, instructor, credit))
    return courses

def click_next_page(current_page):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagination_row = soup.find('table', {'id': 'ctl00_ContentPlaceHolder1_grv_course'}).find_all('tr')[0]  # 找到包含页码的行
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
        elif link.text.strip() == "...":
            if current_page % 10 == 0:
                next_page_button = driver.find_elements(By.LINK_TEXT, "...")[-1]
                next_page_button.click()
                return True
    return False

# scratch the first page
all_courses = []
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
first_page = extract_courses(soup)
# print(first_page)
all_courses.extend(first_page)

# initialize current_page number
current_page = 1

# scratch all the pages
while True:
    if click_next_page(current_page):
        time.sleep(2)  # adjust depending on needs
        current_page += 1
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        page_courses = extract_courses(soup)
        if len(page_courses) == 0:
            raise Exception("Not able to load the page. Please increase sleep time or check your internet connection.")
        except Exception as e:
            print(f"Error: {e}")
            print(f"Page{current_page} failed")
        # print(page_courses)
        print(f"Page{current_page} completed")
        all_courses.extend(page_courses)
    else:
        print("All pages completed")
        break

# Save all course information to a local SQLite database
conn = sqlite3.connect('course offering.db')
c = conn.cursor()

# Create a table to store the course information
c.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status INTEGER,
        rgno TEXT,
        season TEXT,
        ay INTEGER,
        course_no TEXT,
        major TEXT,
        level TEXT,
        lang TEXT,
        title_j TEXT,
        title_e TEXT,
        schedule TEXT,
        room TEXT,
        instructor TEXT,
        unit INTEGER
    )
''')

# Insert course data into the table
for course in all_courses:
    c.execute('INSERT INTO courses (status, reno, season, ay, course_no, major, level, lang, '
              'title_j, title_e, schedule, room, instructor, unit) '
              'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', course)

# Commit the changes and close the connection
conn.commit()
conn.close()
print("Database updated.")

# close chrome driver
driver.quit()
