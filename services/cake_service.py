from src.models.profile import Profile, Experience, Education, Certificate, Language
from src.services.browserless import browserless_pdf
from src.utils.file_utils import sanitize_filename, save_link_to_csv, get_data_from_col_from_csv
from src.models.job_description import JobDescription
from urllib.parse import quote
from googleapiclient.discovery import build
import os
import requests
from bs4 import BeautifulSoup
from pyppeteer import launch

class JobDescriptionCake(JobDescription):
    def __init__(self, url: str, category: str = "N/A", file_log_name: str = "error_logs.txt"):
        super().__init__(url, category)
        self.file_log_name = file_log_name
    
    def crawl_job(self):
        headers = {
            "Accept-Language": "en;p=1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        }
        response = requests.get(self.data["Job URL"], headers=headers, cookies={})
        response.raise_for_status()  

        soup = BeautifulSoup(response.text, 'html.parser')

        self.get_company_info(soup)
        self.get_job_title(soup)
        self.get_date_posted(soup)
        self.get_work_type(soup)
        self.get_time_type_and_level(soup)
        self.get_description(soup)
        
        job_detail = self.to_dict()
        return job_detail

    def get_company_info(self, soup):
        try:
            company_name = soup.find('div', class_='JobDescriptionLeftColumn_companyInfo__prhLY').find('a', class_='JobDescriptionLeftColumn_name__ABAp9').get_text(strip=True)
            self.set_field("Company Name", company_name)

            company_url = "https://www.cake.me" + soup.find('div', class_='JobDescriptionLeftColumn_companyInfo__prhLY').find('a', class_='JobDescriptionLeftColumn_name__ABAp9').get('href')
            self.set_field("Company URL", company_url)
        except:
            self.set_field("Company Name", "")
            self.set_field("Company URL", "")
        
        try:
            location = soup.find('div', class_='JobDescriptionRightColumn_jobInfo__9Liba').find_all('div', class_='JobDescriptionRightColumn_row__5rklX', recursie=False)[1].get_text(strip=True)
            self.set_field("Location", location)
        except:
            self.set_field("Location", "")
    
    def get_job_title(self, soup):
        try:
            job_title = soup.find('div', class_='JobDescriptionLeftColumn_titleRow__ld40x').get_text(strip=True)
            self.set_field("Job Title", job_title)
        except:
            self.set_field("Job Title", "")
    
    def get_date_posted(self, soup):
        try:
            date_posted = soup.find('div', class_='InlineMessage_label__LJGjW').get_text(strip=True)
            self.set_field("Date Posted", date_posted)
        except:
            self.set_field("Date Posted", "")
    
    def get_work_type(self, soup):
        try:
            work_type = next((div for div in soup.find_all("div", class_="JobDescriptionRightColumn_row__5rklX") 
                                    if div.find("li", class_="fa-house")), None).get_text(strip=True)
            self.set_field("Work Type", work_type)
        except:
            try:
                work_type = next((div for div in soup.find_all("div", class_="JobDescriptionRightColumn_row__5rklX") 
                                    if div.find("i", class_="fa-house")), None).get_text(strip=True)
                self.set_field("Work Type", work_type)
            except:
                self.set_field("Work Type", "")
    
    def get_time_type_and_level(self, soup):
        try:
            time_type = soup.find('div', class_='JobDescriptionRightColumn_jobInfo__9Liba').find_all('div', class_='JobDescriptionRightColumn_row__5rklX', recursive=False)[0].get_text(strip=True).split("・")[0]
            if time_type in ["Full-time", "Part-time", "Internship", "Contract", "Freelance"]:
                self.set_field("Time Type", time_type)
            else:
                self.set_field("Time Type", "")
        except:
            self.set_field("Time Type", "")
        
        try:
            level = soup.find('div', class_='JobDescriptionRightColumn_jobInfo__9Liba').find_all('div', class_='JobDescriptionRightColumn_row__5rklX', recursive=False)[0].get_text(strip=True).split("・")[1]
            self.set_field("Job Level", level)
        except:
            level = soup.find('div', class_='JobDescriptionRightColumn_jobInfo__9Liba').find_all('div', class_='JobDescriptionRightColumn_row__5rklX', recursive=False)[0].get_text(strip=True).split("・")[0]
            if level in ["Internship", "Entry level", "Assistant", "Mid-Senior level", "Director", "Executive (VP, GM, C-Level)"]:
                self.set_field("Job Level", level)
            else:
                self.set_field("Job Level", "")
    
    def get_description(self, soup):
        try:
            description = "".join(
                                        div.get_text(strip=True, separator="\n") for div in soup.find_all('div', class_='ContentSection_contentSection__ELRlG')
                                        )

            self.set_field("Job Description", description)
        except:
            self.set_field("Job Description", "")

class ProfileCake(Profile):
    def __init__(self, url: str, file_log_name: str = "error_logs.txt"):
        if "?locale=en" not in url:
            url = url + "?locale=en"
            
        super().__init__(url)
        self.link_resume = "N/A"
        self.file_log_name = file_log_name
    
    def crawl_profile(self):
        headers = {
            "Accept-Language": "en;p=1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        }
        response = requests.get(self.data["linkedin_url"], headers=headers, cookies={})
        response.raise_for_status()  

        soup = BeautifulSoup(response.text, 'html.parser')

        self.get_link_resume(soup)
        self.get_name(soup)
        self.get_location(soup)
        self.get_job_title(soup)
        self.get_about(soup)
        self.get_experiences(soup)
        self.get_educations(soup)
        self.get_skills(soup)
        self.get_languages(soup)
        self.get_certificates(soup)

        return self.to_dict(), self.link_resume
    
    def get_link_resume(self, soup):
        try:
            link_resume = soup.find('div', class_='SidebarMenu_menu__X1VxI').find('a', string='Resume').get('href')
            self.link_resume = link_resume
        except:
            try:
                link_resume = "https://www.cake.me/" + soup.find('div', class_='UserProfilePage_headerActions__TylT_').find('a', rel='noreferrer noopener').get('href').split('?')[0] + "?locale=en"
                self.link_resume = link_resume
            except:
                self.link_resume = ""

    def get_name(self, soup):
        try:
            name = soup.find('h2', class_='UserProfileHeader_name__knPil').get_text(strip=True)
            self.set_field("name", name)
        except:
            self.set_field("name", "")
    
    def get_location(self, soup):
        try:
            location = soup.find('div', class_='UserProfileHeader_contentSecondary__nQv3X').find_all('div', recursive=False)[2].get_text(strip=True)
            self.set_field("location", location)
        except:
            self.set_field("location", "")
    
    def get_job_title(self, soup):
        try:
            job_title = soup.find('div', string='Desired positions').find_parent().find_all('div', recursive=False)[1].get_text(strip=True)
            self.set_field("job_title", job_title)
        except:
            self.set_field("job_title", "")
    
    def get_about(self, soup):
        try:
            about = soup.find('div', class_='UserProfileHeader_description__D9eaV').get_text(strip=True, separator="\n")
            self.set_field("about", about)
        except:
            self.set_field("about", "")
    
    def get_experiences(self, soup):
        try:
            divs_experience = soup.find('div', class_='WorkExperienceList_list__NZHgH').find_all('div', recursive=False)
        except:
            divs_experience = []
        
        if len(divs_experience) > 0:
            for div_experience in divs_experience:
                try:
                    position_title = div_experience.find('h4', class_='WorkExperienceListItem_title__V1121').get_text(strip=True, separator="\n")
                except:
                    position_title = ""

                try:
                    institution_name = div_experience.find('a', class_='WorkExperienceListItem_organizationName__Fnm_Q').get_text(strip=True)
                except:
                    institution_name = ""

                try:
                    linkedin_url = "https://www.cake.me" + div_experience.find('a', class_='WorkExperienceListItem_organizationName__Fnm_Q').get('href')
                except:
                    linkedin_url = ""

                try:
                    from_date = div_experience.find('div', class_='WorkExperienceListItem_meta__2HENv').get_text(strip=True).split('-')[0].strip()
                except:
                    from_date = ""

                try:
                    to_date = div_experience.find('div', class_='WorkExperienceListItem_meta__2HENv').get_text(strip=True).split('-')[1].split('・')[0].strip()
                except:
                    to_date = ""

                try:
                    duration = div_experience.find('div', class_='WorkExperienceListItem_meta__2HENv').get_text(strip=True).split('・')[1].strip()
                except:
                    duration = ""

                try:
                    location = div_experience.find('div', class_='WorkExperienceListItem_locationSegments__GZbl8').get_text(strip=True)
                except:
                    location = ""

                try:
                    description = div_experience.find('div', class_='WorkExperienceListItem_description__mVdAF').get_text(strip=True, separator="\n")
                except:
                    description = ""

                self.add_experience(Experience(position_title, institution_name, linkedin_url, from_date, to_date, duration, location, description))
    
    def get_educations(self, soup):
        try:
            divs_education = soup.find('div', class_='EducationList_list__icyX6').find_all('div', recursive=False)
        except:
            divs_education = []
        
        if len(divs_education) > 0:
            for div_education in divs_education:
                try:
                    institution_name = div_education.find('h4', class_='EducationListItem_title__hCof4').find('a', rel='noreferrer noopener').get_text(strip=True)
                except:
                    institution_name = ""

                try:
                    linkedin_url = "https://www.cake.me" + div_education.find('h4', class_='EducationListItem_title__hCof4').find('a', rel='noreferrer noopener').get('href')
                except:
                    linkedin_url = ""

                try:
                    degree = div_education.find('div', class_='EducationListItem_subtitle__2k8Hg').get_text(strip=True)
                except:
                    degree = ""
                
                try:
                    from_date = div_education.find('div', class_='EducationListItem_meta__YTfY5').get_text(strip=True).split('-')[0].strip()
                except:
                    from_date = ""
                
                try:
                    to_date = div_education.find('div', class_='EducationListItem_meta__YTfY5').get_text(strip=True).split('-')[1].strip()
                except:
                    to_date = ""
                
                try: 
                    description = div_education.find('h5', text="Description").parent.get_text(strip=True, separator="\n")
                except:
                    description = ""

                try:
                    skills = description.split("Skills: ")[1]
                except:
                    skills = ""
                
                self.add_education(Education(institution_name, degree, linkedin_url, from_date, to_date, description, skills))
    
    def get_skills(self, soup):
        try:
            divs_skill = soup.find('div', class_="ProfessionalBackground_itemLabel__WII9I", text="Skills").parent.find_all('div', recursive=False)[1].find('div', recursive=False)
        except:
            divs_skill = []
        
        if len(divs_skill) > 0:
            for div_skill in divs_skill:
                try:
                    self.add_skill(div_skill.get_text(strip=True))
                except:
                    pass
    
    def get_languages(self, soup):
        try:
            divs_language = soup.find('div', class_="ProfessionalBackground_itemLabel__WII9I", text="Languages").parent.find_all('div', recursive=False)[1]
        except:
            divs_language = []
        
        if len(divs_language) > 0:
            for div_language in divs_language:
                try:
                    language_name = div_language.get_text(strip=True).split('・')[0] or ""
                    proficiency = div_language.get_text(strip=True).split('・')[1] or ""

                    self.add_language(Language(language_name, proficiency))
                except:
                    pass
    
    def get_certificates(self, soup):
        try:
            divs_certificate = soup.find('div', class_="CertificationList_list__9aoRC").find_all('div', recursive=False)
        except:
            divs_certificate = []
        
        if len(divs_certificate) > 0:
            for div_certificate in divs_certificate:
                try:
                    certificate_name = div_certificate.find('div', class_='CertificationListItem_header__75WBL').get_text(strip=True)
                except:
                    certificate_name = ""
                
                try:
                    institution_name = div_certificate.find('div', class_='CertificationListItem_subtitle__nVvbS').get_text(strip=True)
                except:
                    institution_name = ""
                
                try:
                    cert_date = div_certificate.find('div', class_='CertificationListItem_meta__hu8ie').get_text(strip=True)
                except:
                    cert_date = ""

                self.add_certificate(Certificate(certificate_name, cert_date, institution_name))

def crawl_job_listings(
                            keyword: str, 
                            location: str, 
                            max_pages: int = 100, 
                            max_jobs: int = 25, 
                            file_log_name: str = "error_logs.txt"
                        ) -> list:
    links = []
    url = f"https://www.cake.me/jobs/{quote(keyword)}?location_list[0]={location}" 

    for page in range(1, max_pages + 1):
        url_page = f"{url}&page={page}"
        # Only log if file_log_name is not None
        if file_log_name:
            from src.utils.file_utils import log_error
            log_error(f"Scraping url:  {url_page}...", file_log_name)
        headers = {
            "Accept-Language": "en;p=1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        }

        try:
            response = requests.get(url_page, headers=headers, cookies={})
            response.raise_for_status()  
            soup = BeautifulSoup(response.text, 'html.parser')

            div_tags = soup.find_all("div", class_="JobSearchItem_container__oKoBL")

            # Get job links
            hrefs = [
                "https://www.cake.me" + a["href"] + "?locale=en" for div in div_tags 
                for a in div.find_all("a", class_="JobSearchItem_jobTitle__bu6yO") 
                if a.has_attr("href")
            ]
            if file_log_name:
                from src.utils.file_utils import log_error
                log_error(f"Found {len(hrefs)} job listings on page {page}.", file_log_name)
            links.extend(hrefs)

            if len(links) >= max_jobs:
                break

        except Exception as e:
            if file_log_name:
                from src.utils.file_utils import log_error
                log_error(f"An error occurred: {e}", file_log_name)
            return links[:min(max_jobs, len(links))]
    
    return links[:min(max_jobs, len(links))]

async def html_to_pdf(
    link_origin: str,
    url: str,
    output_folder_path: str = "data",
):
    """
    Convert a webpage to PDF using browserless, saving to output_folder_path.
    """
    if "?locale=en" not in url:
        url = url + "?locale=en"

    # Use sanitized file name for the PDF
    from src.utils.file_utils import sanitize_filename
    file_name = sanitize_filename(link_origin)
    pdf_output_path = browserless_pdf(url, output_folder_path, file_name)
    print(f"PDF file {file_name} has been saved at {pdf_output_path}.")



def google_search(query: str, start: str, api_key: str, search_engine_id: str) -> list:
    try:
        service = build("customsearch", "v1", developerKey=api_key)
        response = service.cse().list(
            q=query,
            cx=search_engine_id,
            start=start,
            num=10  
        ).execute()
        return [item['link'] for item in response.get('items', [])]
    except Exception as err:
        print(f"An error occurred: {err}")
        return []

def crawl_links_person_cake_google(
                                        keyword: str, 
                                        location: str, 
                                        max_links_person: int = 20, 
                                        links_person_file: str = "data/links_person.csv", 
                                        file_log_name: str = "error_logs.txt",
                                        api_key: str = "AIzaSyB5NzNEv80vlBEim240j-wd15xPwb6SCkM",
                                        search_engine_id: str = "a07066d98ad044fe0"
                                    ) -> list: 
    
    query = f'"{keyword}"'
    if location != "":
        query = f'"{keyword}", "{location}"'

    # Only log if file_log_name is not None
    if file_log_name:
        from src.utils.file_utils import log_error
        log_error(f"Searching for {query}...", file_log_name)

    all_links = []
    if os.path.exists(links_person_file):
        all_links_pre = get_data_from_col_from_csv(links_person_file, "Link")
    else:
        all_links_pre = []

    start = 0  
    while len(all_links) < max_links_person:
        links = google_search(query, start, api_key, search_engine_id)
        if not links:
            if file_log_name:
                from src.utils.file_utils import log_error
                log_error("No more links found.", file_log_name)
            break

        if links:
            for link in links:
                link = link.split('?')[0] + "?locale=en"
                
                if link not in all_links:
                    if link not in all_links_pre:
                        save_link_to_csv(link, keyword, location, filename = links_person_file)  
                        all_links.append(link)
                        if len(all_links) >= max_links_person:
                            break

        if len(links) == 0:
            if file_log_name:
                from src.utils.file_utils import log_error
                log_error("No more links found.", file_log_name)
            break

        start += 10

    return all_links[:min(max_links_person, len(all_links))]