import unittest, httpx, json
from structs import Resume, Vacancy

def get(path):
    r = httpx.get(f'http://localhost:8000{path}', timeout=60.0)
    return r.json()

class TestVacancies(unittest.TestCase):
    def test_00_search_basic(self):
        r = get('/search/vacancies')
        self.assertIsInstance(r, list)
        for item in r:
            self.assertIsInstance(item, dict)
            keys = item.keys()
            self.assertIn('id', keys)
            self.assertIn('name', keys)
            self.assertIn('area', keys)
            self.assertIn('type', keys)
            self.assertIn('employer', keys)
            self.assertIn('responsibility', keys)
            self.assertIn('schedule', keys)
            self.assertIn('experience', keys)
            self.assertIn('employment', keys)
            self.assertIn('requirement', keys)
            self.assertIn('currency', keys)
            self.assertIn('average_salary', keys)

    def test_01_search_positive(self):
        r = get('/search/vacancies?experience=noExperience&schedule=flexible&employment=part')
        self.assertIsInstance(r, list)
        for item in r:
            self.assertEqual(item['schedule'], 'Гибкий график')
            self.assertEqual(item['employment'], 'Частичная занятость')
            self.assertEqual(item['experience'], 'Нет опыта')

    def test_02_search_negative(self):
        r = httpx.get(f'http://localhost:8000/search/vacancies?page=999')
        self.assertEqual(r.status_code, 500)

    def test_03_db_basic(self):
        r = get('/db/vacancies')
        self.assertIsInstance(r, list)
        for item in r:
            self.assertIsInstance(item, dict)
            keys = item.keys()
            self.assertIn('id', keys)
            self.assertIn('name', keys)
            self.assertIn('area', keys)
            self.assertIn('type', keys)
            self.assertIn('employer', keys)
            self.assertIn('responsibility', keys)
            self.assertIn('schedule', keys)
            self.assertIn('experience', keys)
            self.assertIn('employment', keys)
            self.assertIn('requirement', keys)
            self.assertIn('currency', keys)
            self.assertIn('average_salary', keys)

    def test_04_db_positive(self):
        r = get('/db/vacancies?page=0&filter={%22experience%22:[{%22text%22:%22%D0%9D%D0%B5%D1%82%20%D0%BE%D0%BF%D1%8B%D1%82%D0%B0%22}],%22schedule%22:[{%22text%22:%22%D0%93%D0%B8%D0%B1%D0%BA%D0%B8%D0%B9%20%D0%B3%D1%80%D0%B0%D1%84%D0%B8%D0%BA%22}],%22average_salary%22:[{%22text%22:%22%%22,%22ordering%22:%22desc%22}]}')
        for i in range(len(r)):
            self.assertEqual(r[i]['schedule'], 'Гибкий график')
            self.assertEqual(r[i]['experience'], 'Нет опыта')
            if i == len(r) - 1:
                continue
            self.assertGreaterEqual(r[i]['average_salary'], r[i+1]['average_salary'])

    def test_05_db_negative(self):
        r = get('/db/vacancies?page=0&filter={%22id%22:[{%22text%22:%22123%22}],%22type%22:[{%22text%22:%22123%22}],%22currency%22:[{%22text%22:%22123%22}]}')
        self.assertEqual(r, [])
            
class TestResumes(unittest.TestCase):
    def test_00_search_basic(self):
        r = get('/search/resumes')
        self.assertIsInstance(r, list)
        for item in r:
            self.assertIsInstance(item, dict)
            keys = item.keys()
            self.assertIn('id', keys)
            self.assertIn('gender', keys)
            self.assertIn('birthday', keys)
            self.assertIn('search_status', keys)
            self.assertIn('address', keys)
            self.assertIn('position', keys)
            self.assertIn('about', keys)
            self.assertIn('currency', keys)
            self.assertIn('preferred_commute_time', keys)
            self.assertIn('moving_status', keys)
            self.assertIn('citizenship', keys)
            self.assertIn('specializations', keys)
            self.assertIn('languages', keys)
            self.assertIn('schedule', keys)
            self.assertIn('skills', keys)
            self.assertIn('employment', keys)
            self.assertIn('education', keys)
            self.assertIn('age', keys)
            self.assertIn('salary', keys)

    def test_01_search_positive(self):
        r = get('/search/resumes?employment=part&schedule=fullDay%2Cflexible')
        self.assertIsInstance(r, list)
        for item in r:
            self.assertTrue(('гибкий график' in item['schedule']) or ('полный день' in item['schedule']) or ('flexible' in item['schedule']) or ('full day' in item['schedule']))
            self.assertTrue(('частичная занятость' in item['employment']) or ('part time' in item['employment']))

    def test_02_search_negative(self):
        r = httpx.get(f'http://localhost:8000/search/vacancies?salary=abc')
        self.assertEqual(r.status_code, 422)

    def test_03_db_basic(self):
        r = get('/db/resumes')
        self.assertIsInstance(r, list)
        for item in r:
            self.assertIsInstance(item, dict)
            keys = item.keys()
            self.assertIn('id', keys)
            self.assertIn('gender', keys)
            self.assertIn('birthday', keys)
            self.assertIn('search_status', keys)
            self.assertIn('address', keys)
            self.assertIn('position', keys)
            self.assertIn('about', keys)
            self.assertIn('currency', keys)
            self.assertIn('preferred_commute_time', keys)
            self.assertIn('moving_status', keys)
            self.assertIn('citizenship', keys)
            self.assertIn('specializations', keys)
            self.assertIn('languages', keys)
            self.assertIn('schedule', keys)
            self.assertIn('skills', keys)
            self.assertIn('employment', keys)
            self.assertIn('education', keys)
            self.assertIn('age', keys)
            self.assertIn('salary', keys)

    def test_04_db_positive(self):
        r = get('/db/resumes?page=0&filter={%22employment%22:[{%22text%22:%22%%D1%87%D0%B0%D1%81%D1%82%D0%B8%D1%87%D0%BD%D0%B0%D1%8F%20%D0%B7%D0%B0%D0%BD%D1%8F%D1%82%D0%BE%D1%81%D1%82%D1%8C%%22}],%22age%22:[{%22text%22:%22%%22,%22ordering%22:%22desc%22}]}')
        for i in range(len(r)):
            self.assertIn('частичная занятость', r[i]['employment'])
            if i == len(r) - 1:
                continue
            self.assertGreaterEqual(r[i]['age'], r[i+1]['age'])

    def test_05_db_negative(self):
        r = get('/db/resumes?page=0&filter={%22age%22:[{%22text%22:%22abc%22}]}')
        self.assertEqual(r, [])

if __name__ == '__main__':
    unittest.main()
