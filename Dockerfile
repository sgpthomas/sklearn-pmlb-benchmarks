FROM ubuntu:16.04

# install software
RUN apt-get update && apt-get install -y python3 python3-pip git
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

# make directorys
RUN mkdir -p /user_dev
RUN mkdir -p /output

# temporary
ENV D3MOUTPUTDIR "/output"

# copy start directory
COPY d3mStart.sh /user_dev
RUN chmod a+x /user_dev/d3mStart.sh

# COPY example.py /user_dev
ADD src/ /user_dev/src/

ENTRYPOINT ["/user_dev/d3mStart.sh"]
