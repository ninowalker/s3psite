.PHONY: clean env/bin/activate

default: env

-include .creds

export BUCKET
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN

env: env/bin/activate | bin

bin: env/bin/activate
	ln -fs env/bin .

env/bin/activate: requirements.txt setup.py
	test -d env || virtualenv --no-site-packages env
	. env/bin/activate; pip install -r requirements.txt
	touch $@

run:
	. env/bin/activate; FLASK_DEBUG=1 FLASK_APP=s3psite python -m flask run 
