Firefox Test Engineering Test Results
=====================================

This project simply generates a HTML report from the Firefox Test Engineering
automated test results submitted to ActiveData. To generate a report, run
`python generate.py path/to/report.html` with the necessary dependencies
installed, or use the Docker image by running
`docker run -v $PWD:/out davehunt/fxtest-report`.
