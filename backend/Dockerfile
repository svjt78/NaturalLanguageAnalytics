# backend/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 1. Copy requirements and install them all in one go
#    (requirements.txt now includes asyncpg, watchdog, and everything else)
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 2. Copy the rest of your backend source
COPY . .

# 3. Expose the FastAPI port
EXPOSE 8000

# 4. Run Uvicorn with reload, binding to 0.0.0.0
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
