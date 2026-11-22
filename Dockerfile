FROM python:3.11-slim

# Buat user non-root sesuai standar keamanan Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Instal library Python
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Salin seluruh kode aplikasi, templates, dan folder assets
COPY --chown=user . /app

# Jalankan FastAPI pada port 7860
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]