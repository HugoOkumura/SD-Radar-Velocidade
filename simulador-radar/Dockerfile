FROM python:3.12-slim

WORKDIR /app

COPY requrirements.txt .
RUN pip3 install -r requrirements.txt

COPY . .

CMD ["python3", "simulador.py"]