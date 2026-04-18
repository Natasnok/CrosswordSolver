FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TESSERACT_CMD=/usr/bin/tesseract

<<<<<<< HEAD:DockerFile
CMD ["gunicorn", "backend.Main:app", "--bind", "0.0.0.0:5000"]
=======
CMD ["gunicorn", "backend.Main:app", "--bind", "0.0.0.0:5000"]
>>>>>>> a50c1280cfb10781f391c1f7513e6f1abfdc40af:Dockerfile
