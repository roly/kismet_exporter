FROM python:3.12-slim

COPY requirements.txt /kis_exp/requirements.txt
RUN pip install --no-cache-dir -r /kis_exp/requirements.txt

COPY kismet_exporter.py /kis_exp/
COPY pd_lookup /kis_exp/pd_lookup/

WORKDIR /kis_exp
CMD [ "python", "kismet_exporter.py" ]
EXPOSE 8501
