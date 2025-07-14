# TRADER/Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

# תיקון: הוספת הדגל --preload כדי למנוע אתחולים מרובים
CMD ["gunicorn", "--bind", "0.0.0.0:7070", "--workers", "3", "--preload", "main:application"]