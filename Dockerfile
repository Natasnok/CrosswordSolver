FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    cmake \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/jsgonsette/Wizium.git /tmp/Wizium \
    && mkdir /tmp/Wizium/build \
    && cd /tmp/Wizium/build \
    && cmake ../Sources/ \
    && make \
    && mkdir -p /app/backend/Generateur/Wizium/Binaries/Linux \
    && cp /tmp/Wizium/build/libWizium*.so /app/backend/Generateur/Wizium/Binaries/Linux/libWizium_x64.so \
    && rm -rf /tmp/Wizium

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV TESSERACT_CMD=/usr/bin/tesseract

CMD ["sh", "-c", "gunicorn backend.Main:app"]