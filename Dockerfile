FROM heroku/heroku:16

# Install pip and opencv
RUN apt-get update && apt-get install -y python-pip libsm6

# Install dependencies
ADD ./webapp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -q -r /tmp/requirements.txt

# Add our code
ADD ./webapp /opt/webapp/
WORKDIR /opt/webapp

# Expose is NOT supported by Heroku
# EXPOSE 5000

# Run the image as a non-root user
RUN useradd -m myuser
USER myuser

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku
CMD gunicorn --bind 0.0.0.0:$PORT wsgi
