FROM python:3

RUN pip3 install prometheus_client
RUN pip3 install python-dateutil
RUN pip3 install kismet_rest

COPY kismet_exporter.py /kis_exp/
COPY pd_lookup /kis_exp/pd_lookup/

CMD [ "python", "./kis_exp/kismet_exporter.py" ]
EXPOSE 8501 
