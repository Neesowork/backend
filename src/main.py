import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from contextlib import asynccontextmanager
from multiprocessing import Process, Queue, Event, Lock

from src.parse import ParserInstance
from src.db import DatabaseWorker
from src.structs import Vacancy, Resume

db, parser = None, None

processes_stop = Event()

stdout_lock = Lock() 

resumes_db_queue, vacancies_db_queue = Queue(), Queue()

def load_config(file_path):
    with open(file_path) as f:
        config = json.loads(f.read())
    return config

def push_resumes(stop_event, stdout_lock, queue):
    db = DatabaseWorker(load_config('./db_config.json'))

    while not stop_event.is_set():
        params = queue.get()
        if not params: # Stop if None
            break
        try:
            db.add_resume(id=params['id'],
                          gender=params['gender'],
                          birthday=params['birthday'],
                          address=params['address'],
                          position=params['position'],
                          search_status=params['search_status'],
                          about=params['about'],
                          preferred_commute_time=params['preferred_commute_time'],
                          moving_status=params['moving_status'],
                          citizenship=params['citizenship'],
                          salary=params['salary'],
                          currency=params['currency'],
                          age=params['age'], 

                          specializations=to_json(params['specializations']), 
                          skills=to_json(params['skills']), 
                          employment=to_json(params['employment']),
                          languages=to_json(params['languages']), 
                          education=to_json(params['education']), 
                          schedule=to_json(params['schedule']))
        except Exception as exc:
            with stdout_lock:
                print('Error adding entry: ', exc, '\nSkipping')

def push_vacancies(stop_event, stdout_lock, queue):
    db = DatabaseWorker(load_config('./db_config.json'))

    while not stop_event.is_set():
        params = queue.get()
        if params == None:
            break

        try:
            db.add_vacancy(id=params['id'], 
                           name=params['name'], 
                           area=params['area'],
                           average_salary=params['average_salary'], 
                           currency=params['currency'],
                           type=params['type'], 
                           employer=params['employer'], 
                           requirement=params['requirement'],
                           responsibility=params['responsibility'],
                           schedule=params['schedule'], 
                           experience=params['experience'],
                           employment=params['employment'])
        except Exception as exc:
            with stdout_lock:
                print('Error adding entry: ', exc, '\nSkipping')

procs = {
    "resumes": Process(target=push_resumes, args=(processes_stop, stdout_lock, resumes_db_queue)),
    "vacancies": Process(target=push_vacancies, args=(processes_stop, stdout_lock, vacancies_db_queue))
}

def queue_resumes(*args):
    global resumes_db_queue
    for arg in args:
        resumes_db_queue.put_nowait(arg)

def queue_vacancies(*args):
    global vacancies_db_queue
    for arg in args:
        vacancies_db_queue.put_nowait(arg)

def procs_start():
    global procs
    procs['resumes'].start()
    procs['vacancies'].start()

def shutdown():
    global procs, processes_stop

    processes_stop.set()    # Redundant stopper (to avoid while True in the code)
    queue_resumes(None)     # Send exit signal
    queue_vacancies(None)   # Send exit signal

    procs['resumes'].join()
    procs['vacancies'].join()

def init():
    global parser, db

    try:
        db = DatabaseWorker(load_config('db_config.json'))
        parser = ParserInstance(load_config('parse_config.json'))
    except Exception as e:
        print(f'Error:\n-> {e}\nwhile loading config/s and/or modules.')
        exit(-1)

    procs_start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init() # Loads configuration files and starts processes
    yield
    shutdown() # Stops running processes

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, 
                   allow_origins=['*'],
                   allow_credentials=True,
                   allow_methods=['*'],
                   allow_headers=['*'])

@app.get('/search/vacancies')
def search_vacancies(page: int=0, text: str=None, experience: str=None, schedule: str=None, employment: str=None, salary: int=None) -> list[Optional[Vacancy]]:
    vacancies = parser.get_vacancies(page=page, text=text, experience=experience, schedule=schedule, employment=employment, salary=salary)
    if not vacancies:
        raise HTTPException(status_code=500, detail='Failed to parse by requested vacancies\' params')

    queue_vacancies(*vacancies)
    return vacancies

@app.get('/search/resumes')
def search_resumes(page: int=0, text: str=None, experience: str=None, schedule: str=None, salary: int=None, employment: str=None) -> list[Optional[Resume]]:
    resumes = parser.get_resumes(page=page, text=text, experience=experience, schedule=schedule, employment=employment, salary=salary)
    if not resumes:
        raise HTTPException(status_code=500, detail='Failed to parse by requested resumes\' params')

    queue_resumes(*resumes)
    return resumes

@app.get('/db/vacancies')
def default(page: int=0, limit: int=20, filter: str='{}') -> list[Optional[Vacancy]]:
    global db
    return db.get_vacancies_table(page, limit, filter)

@app.get('/db/resumes')
def default(page: int=0, limit: int=20, filter: str='{}') -> list[Optional[Resume]]:
    global db
    return db.get_resumes_table(page, limit, filter)

@app.get('/')
def default() -> dict:
    return {'detail': 'server functional'}

def to_json(obj):
    return json.dumps(obj, ensure_ascii=False)

def count_nones(params):
    count = 0
    for param in params:
        if not params[param]:
            count += 1
    return count