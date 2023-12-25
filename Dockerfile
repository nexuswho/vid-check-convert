# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN chmod 0644 /app/del.sh

RUN apt-get -y install cron

RUN crontab -l | { cat; echo "*/5 * * * * bash /app/del.sh"; } | crontab -

RUN cron


# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

RUN apt update && apt install -y curl ffmpeg

# Make port 80 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
