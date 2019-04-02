FROM python:3.7-alpine

# Alpine Linux's CDN seems to fail on a regular basis.
# Switch to another mirror if it does.
RUN { apk update || sed -i 's/dl-cdn/dl-5/g' /etc/apk/repositories && apk update; } || exit 1

RUN apk add --no-cache ca-certificates bind-tools
RUN apk add --no-cache -U tzdata
RUN cp /usr/share/zoneinfo/UTC /etc/localtime
RUN echo "UTC" >  /etc/timezone

# RUN pip install --upgrade pip
RUN pip install --upgrade requests

COPY ./requirements.txt requirements.txt
RUN pip install -U -r requirements.txt
COPY . /jockbot/
#WORKDIR /jockbot/jockbot_nhl
#RUN python setup.py sdist bdist_wheel && pip install .
#WORKDIR /jockbot/jockbot_mlb
#RUN python setup.py sdist bdist_wheel && pip install .
#RUN cp jockbot_mlb/config.json /usr/local/lib/python3.7/site-packages/jockbot_mlb/config.json

WORKDIR /jockbot
RUN mkdir log

ENTRYPOINT ["python", "/jockbot/jockbot.py"]
