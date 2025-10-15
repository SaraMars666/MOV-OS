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
# Filter out Windows-only TA-Lib wheel if present to avoid build failures in Linux,
# and handle non-UTF8 encodings (e.g., UTF-16) gracefully.
RUN python - <<'PY'
from pathlib import Path
data = Path('requirements.txt').read_bytes()
text = None
for enc in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1'):
    try:
        text = data.decode(enc)
        break
    except Exception:
        pass
if text is None:
    text = data.decode('utf-8', 'ignore')
lines = []
for line in text.splitlines():
    if line.strip().startswith('TA-Lib'):
        continue
    lines.append(line)
Path('requirements.filtered.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY
RUN pip install --no-cache-dir -r requirements.filtered.txt

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
