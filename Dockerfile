FROM python:3.6

MAINTAINER Dave Hunt <dave.hunt@gmail.com>

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY active_data.py generate.py template.html ./

COPY queries ./queries/

RUN mkdir -p /out

VOLUME ["/out"]

CMD python generate.py -o /out/report.html
