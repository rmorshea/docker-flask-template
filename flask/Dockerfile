FROM python:3.6
RUN useradd nginx
RUN mkdir /flask
WORKDIR /flask

ADD requirements.txt /flask/
RUN pip install -r requirements.txt

ADD uwsgi.ini /flask
# ADD project /flask/project
# ADD run.py /flask/

EXPOSE 5000

CMD ["uwsgi", "--ini", "uwsgi.ini"]
