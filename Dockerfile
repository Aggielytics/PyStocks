FROM python:3.9.4-slim

WORKDIR /app

ADD ./src /app

RUN pip install --upgrade pip
RUN pip install -r Requirements.txt

EXPOSE 8080

CMD ["python", "StockDashboard.py"]