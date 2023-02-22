FROM python:3.8-buster
WORKDIR /vanilla_flask

# Copy files
COPY . .

# Install packages
RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install libavcodec-dev libavformat-dev libswscale-dev
RUN apt-get -y install libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev libswscale-dev libxvidcore-dev libx264-dev libxine2-dev
RUN apt-get -y install libgtk-3-dev
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 5000
CMD ["python3", "./app.py"]