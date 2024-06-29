FROM python:3.11.5
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY src ./src
COPY db_config_docker.json ./db_config.json
COPY parse_config.json .

EXPOSE 8000
CMD uvicorn src.main:app --host 0.0.0.0 --port 8000