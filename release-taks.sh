#!/usr/bin/env bash

python manage.py migrate
python manage.py makemigrations housingapp
python manage.py migrate housingapp
python manage.py deleteorphanedmedia --noinput
