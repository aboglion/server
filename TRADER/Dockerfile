FROM python:3.9-slim

WORKDIR /trader_app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

# Change 'app:app' to '[your_filename]:app'
# For example, if your file is main.py, use 'main:app'
CMD ["gunicorn", "--bind", "0.0.0.0:7070", "--workers", "1", "--preload", "main:app"]
