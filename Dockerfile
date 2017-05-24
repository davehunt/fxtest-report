FROM python:3.6

MAINTAINER Dave Hunt <dave.hunt@gmail.com>

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY generate.py template.html ./

RUN mkdir -p /out

VOLUME ["/out"]

CMD python generate.py /out/report.html
