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
# Filter out Windows-only TA-Lib wheel if present to avoid build failures in Linux
RUN python - <<'PY'
from pathlib import Path
lines = []
for line in Path('requirements.txt').read_text().splitlines():
    if line.strip().startswith('TA-Lib'):
        continue
    lines.append(line)
Path('requirements.filtered.txt').write_text('\n'.join(lines) + '\n')
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
