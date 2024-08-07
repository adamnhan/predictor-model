import requests
import pickle
import csv
from bs4 import BeautifulSoup

# Your ScraperAPI key
SCRAPERAPI_KEY = '498940a3436404c80450939d7447a5de'

def save_cookies():
    session = requests.Session()
    login_url = f"http://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url=https://www.researchgate.net/login"
    
    # Manually login to obtain cookies
    response = session.get(login_url)
    print("Login page loaded. Please log in manually and save cookies.")

    # Save cookies
    with open("cookies.pkl", "wb") as file:
        pickle.dump(session.cookies, file)
    print("Cookies saved successfully!")

def load_cookies():
    session = requests.Session()
    with open("cookies.pkl", "rb") as file:
        session.cookies.update(pickle.load(file))
    return session

def scrape_university_researchers(session, base_url):
    researchers = []
    page = 1
    while True:
        url = f"http://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={base_url}/{page}"
        response = session.get(url)
    
        soup = BeautifulSoup(response.text, 'html.parser')
        member_list = soup.select('.institution-members-list .nova-legacy-v-person-list-item')  # Adjust selector based on actual HTML structure
        
        # If no members are found, break the loop
        if not member_list:
            print(f"No members found on page {page}. Ending pagination for {base_url}.")
            break

        for member in member_list:
            # Ensure name is not None
            name_tag = member.select_one('.nova-legacy-v-person-list-item__title a')
            if name_tag:
                name = name_tag.text.strip()
            else:
                print(f"Skipping member without a name on page {page}.")
                continue  # Skip this member if no name is found

            # Initialize department and discipline
            department = None
            discipline = None

            # Search for department and discipline within the same member
            info_sections = member.select('.nova-legacy-v-person-list-item__info-section')
            for section in info_sections:
                title_tag = section.select_one('.nova-legacy-v-person-list-item__info-section-title')
                if title_tag:
                    title = title_tag.text.strip()
                    if title == "Department":
                        department_tag = section.select_one('span')
                        if department_tag:
                            department = department_tag.text.strip()
                    elif title == "Disciplines":
                        disciplines_list = section.select_one('ul')
                        if disciplines_list:
                            disciplines = [li.text.strip() for li in disciplines_list.find_all('li')]
                            discipline = ', '.join(disciplines)

            researchers.append({"name": name, "department": department, "discipline": discipline})

        page += 1 

    return researchers

def save_to_csv(data, filename="researchers.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["name", "department", "discipline"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == "__main__":
    # First-time login to manually solve CAPTCHA and save cookies
    save_cookies()
    
    session = load_cookies()

    university_urls = [
        "https://www.researchgate.net/institution/Universidad_de_Panama2/members",
        "https://www.researchgate.net/institution/Universidad-Tecnologica-de-Panama/members",
        "https://www.researchgate.net/institution/The_Autonomous_University_of_Chiriqui/members",
        "https://www.researchgate.net/institution/Universidad_Catolica_Santa_Maria_la_Antigua/members"
    ]
    
    all_researchers = []
    for base_url in university_urls:
        print(f"Scraping members from {base_url}")
        researchers = scrape_university_researchers(session, base_url)
        all_researchers.extend(researchers)
    
    print(f"Total number of researchers extracted: {len(all_researchers)}")
    
    save_to_csv(all_researchers)
    print("Data saved to researchers.csv")