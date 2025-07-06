FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY init_db.py .

CMD ["python3","init_db.py"]