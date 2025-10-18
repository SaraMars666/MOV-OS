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
# Filter out Windows-only and heavy packages to avoid build failures on slim Linux images.
# This avoids the Windows TA-Lib wheel and large DS/trading stacks not needed at runtime.
RUN grep -Ev "^(TA-Lib|numpy|pandas|scipy|scikit-learn|matplotlib|seaborn|Cython|yfinance|binance-connector|binance-futures-connector|unicorn-binance-rest-api|unicorn-binance-websocket-api|unicorn-fy|diagrams|graphviz|python-pptx|pydocx)\b" requirements.txt > requirements.filtered.txt \
    && pip install --no-cache-dir -r requirements.filtered.txt

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
