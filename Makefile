CWD=$(shell pwd)

export OPSBOT_IMAGE_VERSION=$(shell cat VERSION)

include .env

build:
	docker-compose -f $(CWD)/docker-compose.yml build

test: build
	docker-compose \
		-f $(CWD)/docker-compose.yml \
		run --rm \
		--entrypoint "python /jalbot/test/main.py" \
		jalbot \
		--with-coverage \
		--cover-package=/jalbot/src

deploy:
	ansible-playbook /Users/jgraves/repos/jalbot2/src/ansible/jalbot/main.yml \
	-i src/ansible/hosts \
	--user=ubuntu \
	--key-file=~/.ssh/missingno-aws-dev.pem -b

run:
	docker-compose \
	    -f $(CWD)/docker-compose.yml \
		run --rm \
		--entrypoint "python /jalbot/src/main.py" jalbot

stop:
	docker-compose down
