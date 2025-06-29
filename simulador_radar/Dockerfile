FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
# RUN python3 -m venv ./
RUN pip3 install -r requirements.txt

COPY simulador.py .

CMD [ "python", "simulador.py" ]

