# Neesowork backend
> This is the backend repository of the Neesowork application. See launch instructions and user guide in the [main repository](https://github.com/Neesowork/application).
## Files overview
``src/parse.py`` contains python's code for the parser module


``src/db.py`` contains python's class code for working with MySQL database


``src/main.py`` contains python's FastAPI application's code and integrates both parse.py and db.py


``db_config.json`` contains some setup parameters for the db.py module 


``db_config_docker.json`` contains some setup parameters for the db.py module to be used in Docker container 


(instead of ``db_config.json`` when it is run locally, since the container requires different host address value)
## Built with SQLAlchemy, FastAPI, BeautifulSoup, httpx, and many of python's built-in modules (json, multiprocessing etc.)
