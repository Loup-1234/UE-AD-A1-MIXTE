FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY user/ .
EXPOSE 3203
CMD ["python", "-u", "user.py"]
