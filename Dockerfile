# Core Box - imagem de producao endurecida
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOX_AMBIENTE=producao \
    BOX_DATABASE=/app/data/box.db \
    BOX_UPLOAD_DIR=/app/uploads

WORKDIR /app

# Dependencias primeiro para favorecer cache de build.
COPY requirements.txt ./

RUN python -m pip install --no-cache-dir --upgrade \
      "setuptools>=70.0.0" \
      "wheel>=0.46.2" \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && addgroup --system corebox \
    && adduser --system \
         --ingroup corebox \
         --home /app \
         --no-create-home \
         corebox \
    && mkdir -p /app/data /app/uploads \
    && chown -R corebox:corebox /app

# COPY seletivo: somente o necessario em runtime.
COPY --chown=corebox:corebox app ./app
COPY --chown=corebox:corebox config ./config
COPY --chown=corebox:corebox wsgi.py ./

USER corebox

EXPOSE 8000

HEALTHCHECK \
  --interval=10s \
  --timeout=5s \
  --start-period=15s \
  --retries=6 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "wsgi:app"]
