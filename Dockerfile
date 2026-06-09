FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl git libgl1 libglib2.0-0 poppler-utils ghostscript && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir fastapi uvicorn
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]