#!/bin/bash

# Run supercronic cronjobs in the background
supercronic cronjobs &

# Run gunicorn command in the background
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 999999 app:app

# No need to wait for the commands to finish
