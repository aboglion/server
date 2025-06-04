FROM python:3.10

WORKDIR /app

COPY . /app

# התקנת ספריה נדרשת ל-opencv
RUN apt-get update && apt-get install -y libgl1

# עדכון pip
RUN pip install --upgrade pip

# התקנת PyTorch ו-TorchVision ל-CPU בלבד (ללא CUDA)
RUN pip install --no-cache-dir torch==2.2.2+cpu torchvision==0.17.2+cpu --index-url https://download.pytorch.org/whl/cpu

# התקנת שאר התלויות החיוניות בלבד (עם טווחי גרסאות תקינים)
RUN pip install --no-cache-dir \
    "numpy>=1.25,<2.0" \
    "pillow>=10.0,<11.0" \
    "flask>=3.1,<4.0" \
    "opencv-python-headless>=4.8,<5.0" \
    "transformers>=4.35,<5.0" \
    "ultralytics>=8.3,<9.0" \
    "gunicorn>=21.2,<22.0"

# בדיקת תקינות התקנה (לא חובה)
RUN python -c "import torch; import transformers; import ultralytics; import flask; print('OK')"

# Create a startup script that can choose between Flask and Gunicorn
RUN echo '#!/bin/bash\n\
if [ "$SERVER_TYPE" = "flask" ]; then\n\
  echo "Starting Flask development server..."\n\
  python run.py\n\
else\n\
  echo "Starting Gunicorn production server..."\n\
  gunicorn --bind 0.0.0.0:3000 run:app\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# Use the startup script as the entry point
CMD ["/app/start.sh"]
