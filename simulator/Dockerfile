FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY publish_cgm.py .
CMD ["python", "publish_cgm.py"]
