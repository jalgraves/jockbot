FROM python:3.7-alpine

# Alpine Linux's CDN seems to fail on a regular basis.
# Switch to another mirror if it does.
RUN { apk update || sed -i 's/dl-cdn/dl-5/g' /etc/apk/repositories && apk update; } || exit 1

RUN apk add --no-cache ca-certificates bind-tools
RUN apk add --no-cache -U tzdata
RUN cp /usr/share/zoneinfo/UTC /etc/localtime
RUN echo "UTC" >  /etc/timezone

RUN pip install --upgrade pip
RUN pip install --upgrade requests

ADD . /jalbot/

WORKDIR /jalbot
RUN mkdir log
RUN pip install -r /jalbot/requirements.txt

ENTRYPOINT ["python", "/jalbot/src/main.py"]
