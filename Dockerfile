FROM ubuntu:16.04

# install software
RUN apt update && apt install -y python3 python3-pip git htop
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

# make directorys
RUN mkdir -p /user_dev
RUN mkdir -p /output

# copy start directory
COPY d3mStart.sh /user_dev
RUN chmod a+x /user_dev/d3mStart.sh

# COPY example.py /user_dev
ADD src/ /user_dev/src/

ENTRYPOINT ["/user_dev/d3mStart.sh"]
