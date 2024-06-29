import httpx
from  bs4 import BeautifulSoup

class ParserInstance:
    def __init__(self, config):
        self.get_vacancies_timeout = config['get_vacancies_timeout']
        self.get_resume_timeout = config['get_resume_timeout']
        self.resume_links_timeout = config['resume_links_timeout']
        self.schedule_dict = [{"id":"fullDay","name":"Полный день","uid":"full_day"},
                              {"id":"shift","name":"Сменный график","uid":"shift"},
                              {"id":"flexible","name":"Гибкий график","uid":"flexible"},
                              {"id":"remote","name":"Удаленная работа","uid":"remote"},
                              {"id":"flyInFlyOut","name":"Вахтовый метод","uid":"fly_in_fly_out"}]
        
        self.experience_dict = [{"id":"noExperience","name":"Нет опыта"},
                                {"id":"between1And3","name":"От 1 года до 3 лет"},
                                {"id":"between3And6","name":"От 3 до 6 лет"},
                                {"id":"moreThan6","name":"Более 6 лет"}]
        
        self.employment_dict = [{"id":"full","name":"Полная занятость"},
                                {"id":"part","name":"Частичная занятость"},
                                {"id":"project","name":"Проектная работа"},
                                {"id":"volunteer","name":"Волонтерство"},
                                {"id":"probation","name":"Стажировка"}]

    def get_vacancies(self, page=0, text=None, experience=None, schedule=None, salary=None, employment=None):
        params = f'?page={page}&per_page=20&'

        if experience:
            params += f'experience={experience}&'
        if text:
            params += f'text={text}&'
        if employment:
            for param in employment.split(','):
                params += f'employment={param}&'
        if schedule:
            for param in schedule.split(','):
                params += f'schedule={param}&'
        if salary:
            params += f'salary={salary}&only_with_salary=true&'

        try:
            r = httpx.get('https://api.hh.ru/vacancies' + params[:-1], timeout=self.get_vacancies_timeout)
            return r.json()['items']
        except Exception as exc:
            return None

    def get_resume_links(self, page=0, query_text=''):
        try:
            r = httpx.get(f'https://hh.ru/search/resume' + query_text, follow_redirects=True, params={'page': page})
        except httpx.TimeoutException as exc:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        soup = soup.find(attrs={'data-qa': 'resume-serp__results-search'})
            
        if soup:
            links = []
            for el in soup.find_all('a', attrs={'class': 'bloko-link'}):
                links.append('https://hh.ru' + el['href'])
            return links
        return None

    def get_resumes(self, page=0, text=None, experience=None, schedule=None, salary=None, employment=None):
        params = f'?page={page}&per_page=20&'

        if experience:
            params += f'experience={experience}&'
        if text:
            params += f'text={text}&logic=normal&pos=full_text&exp_period=all_time&'
        if employment:
            for param in employment.split(','):
                params += f'employment={param}&'
        if schedule:
            for param in schedule.split(','):
                params += f'schedule={param}&'
        if salary:
            params += f'salary_from={int(salary - 0.1*salary)}&salary_to={int(salary + 0.1*salary)}&label=only_with_salary&'
        links = self.get_resume_links(query_text=params[:-1])
        
        result = []

        for link in links:
            result.append(self.get_resume_params(link))
        
        return result

    # reformats \xa0 spaces 
    def fix_spaces(text):
        return ' '.join(text.split())

    def get_text_qa(soup, name):
        res = soup.find(attrs={'data-qa': name})
        if res:
            return ParserInstance.fix_spaces(res.text)
        return None

    def get_vacancy_params(self, item):

        params = {
            'id': item['id'],
            'name': item['name'],
            'area': item['area']['name'],
            'average_salary': None,
            'currency': None if not item['salary'] else item['salary']['currency'],
            'type': item['type']['name'],
            'employer': item['employer']['name'],
            'requirement': None,
            'responsibility': item['snippet']['responsibility'],
            'schedule': item['schedule']['name'],
            'experience': item['experience']['name'],
            'employment': item['employment']['name']
        }

        if item['snippet']['requirement']:
            params['requirement'] = item['snippet']['requirement'].replace('<highlighttext>', '').replace('</highlighttext>', '')

        if item['salary']:
            if item['salary']['from']:
                if item['salary']['to']:
                    params['average_salary'] = (int(item['salary']['from']) + int(item['salary']['to'])) // 2
                else:
                    params['average_salary'] = int(item['salary']['from'])
            else:
                params['average_salary'] = int(item['salary']['to'])
        return params

    def get_resume_params(self, resume_link):
        params = {
            'id': None,
            'gender': None,
            'age': None,
            'birthday': None,
            'search_status': None,
            'address': None,
            'position': None,
            'specializations': None,
            'about': None,
            'salary': None,
            'preferred_commute_time': None,
            'skills': None,
            'employment': None,
            'moving_status': None,
            'citizenship': None,
            'languages': None,
            'education': None,
            'work_experience': None,
            'work_prev_pos': None,
            'trips_status': None,
            'schedule': None,
        }

        try:
            r = httpx.get(resume_link, follow_redirects=True, timeout=self.get_resume_timeout)
        except httpx.TimeoutException as exc:
            return params
        
        soup = BeautifulSoup(r.text, 'html.parser')
        if not soup: return None

        params['id'] = resume_link.split('?')[0].split('/')[-1]
        params['gender'] = ParserInstance.get_text_qa(soup, 'resume-personal-gender')
        params['age'] = ParserInstance.get_text_qa(soup, 'resume-personal-age')
        params['birthday'] = ParserInstance.get_text_qa(soup, 'resume-personal-birthday')
        params['search_status'] = ParserInstance.get_text_qa(soup, 'job-search-status')
        params['address'] = ParserInstance.get_text_qa(soup, 'resume-personal-address')
        params['position'] = ParserInstance.get_text_qa(soup, 'resume-block-title-position')
        params['about'] = ParserInstance.get_text_qa(soup, 'resume-block-skills-content')

        data = ParserInstance.get_text_qa(soup, 'resume-block-position-specialization')
        if data:
            params['specializations'] = data.replace(', ', ',').split(',')

        data = ParserInstance.get_text_qa(soup, 'resume-block-salary')
        if data:
            params['salary'] = ''.join(data.split(' ')[:-2])

        data = soup.find('span', attrs={'class': 'resume-block-travel-time'})
        if data:
            params['preferred_commute_time'] = ParserInstance.fix_spaces(data.text)

        data = soup.find(attrs={'data-qa': 'skills-table'})
        if data:
            params['skills'] = list(map(lambda x: ParserInstance.fix_spaces(x.text), data.find_all(attrs={'data-qa': 'bloko-tag__text'})))

        data = soup.find(attrs={'data-qa': 'resume-block-specialization-category'})
        if data:
            params['employment'], params['schedule'] = list(map(lambda x: ''.join(ParserInstance.fix_spaces(x.text).split(':')[1:]).strip().replace(', ', ',').split(','), data.parent.parent.find_all('p')))
            
        data = soup.find(attrs={'data-qa': 'resume-personal-address'})
        if data:
            params['moving_status'], params['trips_status'] = [x.strip() for x in ParserInstance.fix_spaces(data.parent.text).split(',')[-2:]]

        data = soup.find(attrs={'data-qa': 'resume-block-additional'})
        if data:
            params['citizenship'] = list(map(lambda x: ''.join(ParserInstance.fix_spaces(x.text).split(':')[1:]).strip(), data.find_all('p')))[0]

        data = soup.find_all('p', attrs={'data-qa': 'resume-block-language-item'})
        if data:
            params['languages'] = list(map(lambda x: ParserInstance.fix_spaces(x.text), data))        
            
        data = soup.find_all(attrs={'data-qa': 'resume-block-education-name'})
        if data:
            params['education'] = list(zip(list(map(lambda x: ParserInstance.fix_spaces(x.text), data)), list(map(lambda x: ParserInstance.fix_spaces(x.text), soup.find_all(attrs={'data-qa': 'resume-block-education-organization'})))))

        data = soup.find(attrs={'data-qa': 'resume-block-experience'})
        if data:
            params['work_experience'] = ' '.join(data.find('h2').text.split()[2:])

        data = soup.find_all(attrs={'data-qa': 'resume-block-experience-position'})
        if data:
            params['work_prev_pos'] = list(map(lambda x: ParserInstance.fix_spaces(x.text), data))

        return params
