FROM python:3.10-slim

# Install system dependencies + Java + Fontconfig
RUN apt-get update && apt-get install -y \
    ghostscript \
    python3-tk \
    libgl1 \
    default-jre \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir camelot-py[cv]
COPY ./app /app
RUN mkdir -p /out

CMD ["python", "main.py"]