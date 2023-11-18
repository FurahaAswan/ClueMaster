FROM python:3.11.2

ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements-unix.txt

EXPOSE 8000

CMD ['python','manage.py','runserver']