FROM python:3.6

MAINTAINER Dave Hunt <dave.hunt@gmail.com>

RUN pip install --no-cache-dir -r requirements.txt

COPY requirements.txt generate.py template.html ./

RUN mkdir -p /out

VOLUME ["/out"]

CMD python generate.py /out/report.html
