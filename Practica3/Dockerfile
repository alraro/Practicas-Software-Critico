FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app
COPY init_config.py /app

RUN useradd -m alraro
USER alraro

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "main.py"]