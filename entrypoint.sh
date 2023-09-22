#!/bin/sh

exec gunicorn bars_app:app --bind 0.0.0.0:$PORT

