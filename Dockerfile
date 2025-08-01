FROM python:3.12-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential gcc \
  && rm -rf /var/lib/apt/lists/*

# Pyproject dosyalarını kopyala (önce, daha hızlı build için)
COPY pyproject.toml poetry.lock README.md /app/

# Poetry kur ve dependencileri yükle
RUN pip install --no-cache-dir poetry \
  && poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root

# Kaynak kodu kopyala (BÖYLE OLMAZSA module NOT FOUND HATASI ALIRSIN!)
COPY src /app/src

# PYTHONPATH ayarla (container içinde kodu görebilsin diye)
ENV PYTHONPATH=/app/src

# Service env ile çalıştır
CMD ["sh", "-c", "python -m $SERVICE"]
