FROM python:3.8

WORKDIR /code

COPY . .

RUN pip install -r requirements.txt

RUN python setup.py sdist bdist_wheel
