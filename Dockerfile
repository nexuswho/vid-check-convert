# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN chmod 0644 /app/del.sh

RUN apt update && apt -y install cron

RUN crontab -l | { cat; echo "*/5 * * * * bash /app/del.sh"; } | crontab -

RUN cron


# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN pip install gunicorn
RUN apt update && apt update --fix-missing && apt install -y curl ffmpeg --fix-missing




RUN mkdir static

RUN mkdir temp

# Make port 80 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "999999", "app:app"]
