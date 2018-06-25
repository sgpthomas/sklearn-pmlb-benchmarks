FROM ubuntu:16.04
RUN apt-get update && apt-get install -y python3
RUN mkdir -p /user_dev
RUN mkdir -p /output
RUN mkdir -p /input
RUN mkdir -p /work

COPY d3mStart.sh /user_dev
RUN chmod a+x /user_dev/d3mStart.sh

COPY example.py /user_dev

ENTRYPOINT ["/user_dev/d3mStart.sh"]
