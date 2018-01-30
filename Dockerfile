FROM python:3.6

MAINTAINER Dave Hunt <dave.hunt@gmail.com>

WORKDIR /src
COPY Pipfile* /src/
RUN pip install pipenv && \
  pipenv install --system --deploy

COPY active_data.py generate.py template.html /src/
COPY queries /src/queries/

CMD python generate.py -o report.html
