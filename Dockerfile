FROM python:3.8
ENV PYTHONUNBUFFERED 1
RUN mkdir /proxybot
WORKDIR /proxybot
COPY requirements.txt /proxybot/
RUN pip install -r requirements.txt
COPY ./bot/ /proxybot/
EXPOSE 80

CMD python app.py

