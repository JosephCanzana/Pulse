FROM python:3.12-bullseye

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPY app .

CMD ["flask", "--app", "app", "--debug", "run", "--host=0.0.0.0", "--port=5000"]


