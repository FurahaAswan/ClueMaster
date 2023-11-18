FROM python:3.11.2

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN pip install -r requirements-unix.txt

EXPOSE 8000

<<<<<<< HEAD
CMD ["python","cluemaster/manage.py","runserver"]
=======
CMD ['python','manage.py','runserver']
>>>>>>> parent of 0d75755 (Update Dockerfile)
