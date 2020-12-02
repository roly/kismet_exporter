FROM python:3

ADD kismet_exporter.py /

RUN pip3 install prometheus_client
RUN pip3 install python-dateutil
RUN pip3 install kismet_rest
CMD [ "python", "./kismet_exporter.py" ]
EXPOSE 8501 
