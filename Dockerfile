FROM python:3.9
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /proxybot
WORKDIR /proxybot
ARG REQS_FILE=requirements.txt
COPY requirements.txt /proxybot/
COPY requirements-dev.txt /proxybot/
RUN pip install -r $REQS_FILE
EXPOSE 80

CMD python bot/app.py

