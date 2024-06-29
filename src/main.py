import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from multiprocessing import Process, Queue, Event, Lock
import time

from src.parse import ParserInstance
from src.db import DatabaseWorker

def to_json(obj):
    return json.dumps(obj, ensure_ascii=False)

def count_nones(params):
    count = 0
    for param in params:
        if not params[param]:
            count += 1
    return count

db = None
parser = None
e_stop, stdout_lock, procs = None, Lock(), {}
jobstores = {'default': MemoryJobStore()}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone='Europe/Moscow')

resumes_db_queue, vacancies_db_queue = Queue(), Queue()

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
    global e_stop
    global lock
    e_stop = Event()
    procs = {
    "resumes": Process(target=push_resumes, args=(e_stop, stdout_lock, resumes_db_queue)),
    "vacancies": Process(target=push_vacancies, args=(e_stop, stdout_lock, vacancies_db_queue))
    }
    procs['resumes'].start()
    procs['vacancies'].start()

def procs_stop():
    global procs
    global e_stop
    e_stop.set()            # Redundant stopper (to avoid while True in the code)
    queue_resumes(None)     # Send exit signal
    queue_vacancies(None)   # Send exit signal
    procs['resumes'].join()
    procs['vacancies'].join()

def load_configs():
    global parser, app_config, db
    try:
        with open('db_config.json') as f:
            db_config = json.loads(f.read())    
        db = DatabaseWorker(db_config)

        with open('parse_config.json') as f:
            parse_config = json.loads(f.read())
        parser = ParserInstance(parse_config)
    except Exception as e:
        print(f'Error:\n-> {e}\nwhile loading config/s and/or modules.')
        exit(-1)

def push_resumes(stop_event, stdout_lock, queue):
    with open('db_config.json') as f:
        db_config = json.loads(f.read())
    db = DatabaseWorker(db_config)

    while not stop_event.is_set():
        params = queue.get()

        if params == None:
            break

        if not params['salary']:
            params['salary'] = '0U'
        if not params['gender']:
            params['gender'] = 'U'
        if not params['age']:
            params['age'] = '0 U'
            
        currency_cutoff = 1
        while not params['salary'][:-currency_cutoff].isdigit():
            currency_cutoff += 1

        try:
            db.add_resume(params['id'], params['gender'][0], int(params['age'].split()[0]), params['birthday'], params['search_status'], 
                        params['address'], params['position'], to_json(params['specializations']), params['about'], int(params['salary'][:-currency_cutoff]), 
                        params['salary'][-currency_cutoff:], params['preferred_commute_time'], to_json(params['skills']), 
                        to_json(params['employment']), params['moving_status'], params['citizenship'], 
                        to_json(params['languages']), to_json(params['education']), to_json(params['schedule']))
        except Exception as exc:
            with stdout_lock:
                print('Error adding entry: ', exc, '\nSkipping')

def push_vacancies(stop_event, stdout_lock, queue):
    with open('db_config.json') as f:
        db_config = json.loads(f.read())
    db = DatabaseWorker(db_config)

    while not stop_event.is_set():
        params = queue.get()
        if params == None:
            break

        try:
            db.add_vacancy(*[params[i] for i in params.keys()])
        except Exception as exc:
            with stdout_lock:
                print('Error adding entry: ', exc, '\nSkipping')

@scheduler.scheduled_job('interval', seconds=60)
def update_database():
    return

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_configs()
    procs_start()
    scheduler.start()
    yield
    scheduler.shutdown()
    procs_stop()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, 
                   allow_origins=['*'],
                   allow_credentials=True,
                   allow_methods=['*'],
                   allow_headers=['*'])

@app.get('/search/vacancies')
def search_vacancies(page: int=0, text: str=None, experience: str=None, schedule: str=None, employment: str=None, salary: int=None):
    vacancies = parser.get_vacancies(page=page, text=text, experience=experience, schedule=schedule, employment=employment, salary=salary)
    if not vacancies:
        raise HTTPException(status_code=500, detail='Failed to parse by requested vacancies\' params')
    response = []
    for vacancy in vacancies:
        params = parser.get_vacancy_params(vacancy)
        queue_vacancies(params)
        response.append(params)
    return response

@app.get('/search/resumes')
def search_resumes(page: int=0, text: str=None, experience: str=None, schedule: str=None, salary: int=None, employment: str=None):
    response = parser.get_resumes(page=page, text=text, experience=experience, schedule=schedule, employment=employment, salary=salary)
    for params in response:
        queue_resumes(params)
    return response

@app.get('/db/vacancies')
def default(page: int=0, limit: int=20, filter: str='{}'):
    global db
    return db.get_vacancies_table(page, limit, filter)

@app.get('/db/resumes')
def default(page: int=0, limit: int=20, filter: str='{}'):
    global db
    return db.get_resumes_table(page, limit, filter)

@app.get('/')
def default():
    return "Server is functional"