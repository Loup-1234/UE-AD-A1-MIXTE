FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY schedule/ .
EXPOSE 3202
CMD ["python", "-u", "schedule.py"]
