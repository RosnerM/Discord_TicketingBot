#Use python as parent image on Ubuntu container
FROM python:3.10.9-slim


# Copy the current directory contents into the container at /app
COPY . /app
#Set the working directory in the container to be /app
WORKDIR /app

#Upgrade pip so we get latest packages + install requirements to run our applications
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

#Specify command to run on terminal when the container STARTS
CMD ["python3", "bot.py"]
