# TRADER/Dockerfile

# השתמש בגרסת פייתון רזה ויציבה
FROM python:3.9-slim

# קבע את ספריית העבודה בתוך הקונטיינר
WORKDIR /app

# העתק את קובץ הדרישות והתקן את התלויות
# זה ישפר את מהירות הבנייה כי השכבה הזו תישמר במטמון
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# העתק את כל שאר קוד האפליקציה
COPY . .

# הגדר את הפקודה שתרוץ כשהקונטיינר עולה
# Gunicorn יריץ את האובייקט 'application' מהקובץ 'main.py' על פורט 7070
CMD ["gunicorn", "--bind", "0.0.0.0:7070", "--workers", "3", "main:application"]