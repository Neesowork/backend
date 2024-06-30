from sqlalchemy import Table, Column, Integer, MetaData, Text, text, create_engine
from sqlalchemy.dialects.mysql import VARCHAR, MEDIUMTEXT, JSON, TINYTEXT, CHAR, insert
from sqlalchemy_utils import database_exists, create_database

from json import loads

class DatabaseWorker:
    def __init__(self, config):
        self.engine = create_engine(f'mysql+mysqlconnector://{config["user"]}:{config["password"]}@{config["hostname"]}:{config["port"]}/{config["db_name"]}?charset=utf8mb4', echo=config["debug"])

        if not database_exists(self.engine.url):
            create_database(self.engine.url, encoding='utf8mb4')

        self.metadata = MetaData()
        self.resumes_table = Table (
            'resumes',
            self.metadata,
            Column('id', VARCHAR(38), primary_key=True, unique=True),
            Column('gender', TINYTEXT),
            Column('age', Integer),
            Column('birthday',  MEDIUMTEXT),
            Column('search_status', MEDIUMTEXT),
            Column('address', MEDIUMTEXT),
            Column('position', MEDIUMTEXT),
            Column('specializations', JSON),
            Column('about', Text),
            Column('salary', Integer),
            Column('currency', TINYTEXT),
            Column('preferred_commute_time', MEDIUMTEXT),
            Column('skills', JSON),
            Column('employment', MEDIUMTEXT),
            Column('moving_status', MEDIUMTEXT),
            Column('citizenship', MEDIUMTEXT),
            Column('languages', JSON),
            Column('education', JSON),
            Column('schedule', MEDIUMTEXT),
        )

        self.vacancies_table = Table (
            'vacancies',
            self.metadata,
            Column('id', VARCHAR(9), primary_key=True, unique=True),
            Column('name', MEDIUMTEXT),
            Column('area', MEDIUMTEXT),
            Column('average_salary',  Integer),
            Column('currency',  TINYTEXT),
            Column('type', MEDIUMTEXT),
            Column('employer', MEDIUMTEXT),
            Column('requirement', Text),
            Column('responsibility', Text),
            Column('schedule', MEDIUMTEXT),
            Column('experience', MEDIUMTEXT),
            Column('employment', MEDIUMTEXT),
        )

        self.metadata.create_all(self.engine)

    def get_vacancies_table(self, page=0, limit=20, filter={}):
        return self.__db_get_rows(page=page, limit=limit, filter=filter, table='vacancies')

    def get_resumes_table(self, page=0, limit=20, filter={}):
        return self.__db_get_rows(page=page, limit=limit, filter=filter, table='resumes')

    def add_vacancy(self, id, name, area, average_salary, currency, type, employer, requirement, responsibility, schedule, experience, employment):
        with self.engine.connect() as connection:
            insert_query = insert(self.vacancies_table).values (
                id=id, name=name, area=area, average_salary=average_salary, currency=currency, type=type, employer=employer, 
                requirement=requirement, responsibility=responsibility, schedule=schedule, experience=experience, employment=employment
            )

            on_duplicate_query = insert_query.on_duplicate_key_update (
                id=insert_query.inserted.id, name=insert_query.inserted.name, area=insert_query.inserted.area,
                average_salary=insert_query.inserted.average_salary, currency=insert_query.inserted.currency, type=insert_query.inserted.type, 
                employer=insert_query.inserted.employer, requirement=insert_query.inserted.requirement, 
                responsibility=insert_query.inserted.responsibility, schedule=insert_query.inserted.schedule, 
                experience=insert_query.inserted.experience, employment=insert_query.inserted.employment
            )

            connection.execute(on_duplicate_query)
            connection.commit()

    def add_resume(self, id, gender, age, birthday, search_status, address, position, specializations, about, salary, currency, preferred_commute_time, skills, employment, moving_status, citizenship, languages, education, schedule):
        with self.engine.connect() as connection:
            insert_query = insert(self.resumes_table).values (
                id=id, gender=gender, age=age, 
                birthday=birthday, search_status=search_status, address=address, 
                position=position, specializations=specializations, about=about, 
                salary=salary, currency=currency, preferred_commute_time=preferred_commute_time, 
                skills=skills, employment=employment, moving_status=moving_status, 
                citizenship=citizenship, languages=languages, education=education,
                schedule=schedule
            )

            on_duplicate_query = insert_query.on_duplicate_key_update (
                gender=insert_query.inserted.gender, age=insert_query.inserted.age, 
                birthday=insert_query.inserted.birthday, search_status=insert_query.inserted.search_status, 
                address=insert_query.inserted.address, position=insert_query.inserted.position, 
                specializations=insert_query.inserted.specializations, about=insert_query.inserted.about, 
                salary=insert_query.inserted.salary, currency=insert_query.inserted.currency,
                preferred_commute_time=insert_query.inserted.preferred_commute_time, 
                skills=insert_query.inserted.skills, employment=insert_query.inserted.employment, 
                moving_status=insert_query.inserted.moving_status, 
                citizenship=insert_query.inserted.citizenship, 
                languages=insert_query.inserted.languages, education=insert_query.inserted.education,
                schedule=insert_query.inserted.schedule
            )

            connection.execute(on_duplicate_query)
            connection.commit()

    def __db_get_rows(self, page=0, limit=0, filter={}, table='resumes'):
        with self.engine.connect() as connection:
            select_query = self.__build_filtering_query(loads(filter), table) + f' LIMIT {limit} OFFSET {page*limit}'
            return connection.execute(text(select_query)).mappings().all()
        
    def __build_filtering_query(self, filter, table='resumes'):
        select_query = f'SELECT * FROM {table}'
        order_by = []

        if filter:
            select_query += ' WHERE'
            for key in filter:
                for entry in filter[key]:
                    if 'ordering' in entry:
                        order_by.append([key, entry['ordering']])
                    select_query += f' {table}.{key} LIKE \'{entry["text"]}\' OR'
                select_query = select_query[:-2] + 'AND'
            select_query = select_query[:-3]

        if order_by:
            select_query += ' ORDER BY'
            for pair in order_by:
                select_query += f' {table}.{pair[0]} {pair[1].upper()},'
            select_query = select_query[:-1]

        return select_query