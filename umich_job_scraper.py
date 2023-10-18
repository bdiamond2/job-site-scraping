import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from bs4 import BeautifulSoup
import pandas as pd

class UMichJob:
    def __init__(self, job_id):
        self.url = f'https://careers.umich.edu/job_detail/{job_id}/'
        self.job_id = job_id
        self.title = ''
        self.location = ''
        self.reg_temp = ''
        self.dept = ''
        self.start_dt = ''
        self.end_dt = ''
        self.salary_low = ''
        self.salary_high = ''
        self.career_interest = ''
    
    def __str__(self):
        return f'{self.title} ({self.job_id})' if self.title != '' else self.url 
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.url == other.url
    
    def __hash__(self):
        return hash(self.url)


def reached_end(soup):
    end_text = 'There are currently no posted jobs fitting the criteria you selected'
    p_tags = soup.find_all('p')
    for p in p_tags:
        if p != None and end_text in p.text:
            return True
    return False

def get_jobs(career_interest = 'All', page_limit = 50, job_limit = None, title = '', keyword = ''):
    jobs = []
    
    for pageNum in range(0,page_limit):
        print(f'Scanning page {pageNum+1}...')
        
        url = f'https://careers.umich.edu/search-jobs?career_interest={career_interest}&page={pageNum}&title={title}&keyword={keyword}'
        response = requests.get(url, verify=False) # TODO: remove verify=False once their site starts working again
        soup = BeautifulSoup(response.text, 'html.parser')

        if reached_end(soup):
            print(f'Reached the end on page number {pageNum+1}\n')
            break

        a_tags = soup.find_all('a')
        for a in a_tags:
            href = a.get('href')
            if href != None and 'job_detail' in href:
                job_id = href.split('/')[2]
                job = UMichJob(job_id)
                job.title = a.text
                jobs.append(job)
        
        if job_limit != None and len(jobs) >= job_limit:
            break

    return jobs

def get_job_info(job):
    response = requests.get(job.url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    div_tags = soup.find_all('div')
    
    for div in div_tags:
        h3 = div.find('h3')
        if h3 == None:
            continue

        p = div.find('p')
        if p == None:
            continue
            
        h3_text = h3.text.lower()
        p_text = p.text
                
        if 'working title' in h3_text:
            job.title = p_text
        elif 'work location' in h3_text:
            job.location = p_text
        elif 'regular/temporary' in h3_text:
            job.reg_temp = p_text
        elif 'department' in h3_text:
            job.dept = p_text
        elif 'date' in h3_text:
            date_range = p_text.split(' - ')
            try:
                job.start_dt = date_range[0]
                job.end_dt = date_range[1]
            except:
                print('\tError scraping dates')
        elif 'salary' in h3_text:
            salary_range = p_text.split(' - ')
            try:
                job.salary_low = salary_range[0]
                job.salary_high = salary_range[1]
            except:
                print('\tError scraping salary')
        elif 'interest' in h3_text:
            interests = div.find_all('p')
            for i in interests:
                job.career_interest += ';' + i.text
            job.career_interest = job.career_interest[1:]

print("\nSearching IT jobs...")
jobs = get_jobs(career_interest=210)

print("Searching 'analyst' jobs...")
jobs.extend(get_jobs(title='analyst'))

print("Searching 'data' jobs...")
jobs.extend(get_jobs(title='data'))

print("Searching 'python' jobs...")
jobs.extend(get_jobs(keyword='python'))
jobs = list(set(jobs))

print(f'{len(jobs)} jobs found')
print('Scraping job info...')
count = 0
for job in jobs:
    count += 1
    print(f'({count}) {job}')
    get_job_info(job)

job_dicts = []

for job in jobs:
    job_dicts.append(vars(job))
    
df = pd.DataFrame(job_dicts)

df.to_csv('umich_jobs.csv', index=False)