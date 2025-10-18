FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt ./
# 1) Actualiza pip para evitar fallos de instalación en arquitecturas ARM
# 2) Filtra paquetes pesados/no usados (DS/trading) y TA-Lib (wheel de Windows)
# 3) Asegura instalación explícita de dependencias core del proyecto (Django, gunicorn, etc.)
RUN python -m pip install --upgrade pip setuptools wheel \
    && grep -Ev "^(TA-Lib|numpy|pandas|scipy|scikit-learn|matplotlib|seaborn|Cython|yfinance|binance-connector|binance-futures-connector|unicorn-binance-rest-api|unicorn-binance-websocket-api|unicorn-fy|diagrams|graphviz|python-pptx|pydocx)\b" requirements.txt > requirements.filtered.txt \
    && python -m pip install --no-cache-dir -r requirements.filtered.txt \
    && python -m pip install --no-cache-dir \
        Django==5.0.7 \
        gunicorn==23.0.0 \
        whitenoise==6.8.2 \
        psycopg2-binary==2.9.9 \
        djangorestframework==3.15.2 \
        djangorestframework-simplejwt==5.3.1 \
        openpyxl==3.1.5 \
        python-docx==1.1.2 \
        aspose-pdf==25.6.0

# Project files
COPY . .

# Collect static at build (optional)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Entrypoint sets up DB and runs server
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
# Use $PORT if provided by the platform, else 8000. Tune workers/timeout for low-RAM free plans.
ENV WORKERS=2
ENV TIMEOUT=60
CMD ["sh", "-c", "gunicorn MOVOS.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WORKERS:-2} --timeout ${TIMEOUT:-60}"]
