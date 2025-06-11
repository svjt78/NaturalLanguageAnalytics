# frontend/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 1. Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 2. (Optional) Install watchfiles backend so Streamlit can poll for changes reliably
#    Watchfiles is Streamlit’s default file‐watcher under the hood.
RUN pip install --no-cache-dir watchfiles

# 3. Copy your app code
COPY . .

# 4. Expose the port and set the working directory
EXPOSE 8501

# 5. Run Streamlit in polling mode so it detects file changes inside Docker volumes
CMD ["streamlit", "run", "app.py", \
     "--server.port", "8501", \
     "--server.address", "0.0.0.0", \
     "--server.fileWatcherType", "poll"]
