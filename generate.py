from datetime import datetime
import sys

from colour import Color
from humanize import naturaldelta
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import requests


def get_data():
    url = 'http://activedata.allizom.org/query'
    query = """{
    "from":"fx-test",
    "groupby":[
        {"name":"job","value":"run.job_name"},
        {"name":"test_id","value":"test.full_name"},
        {"name":"test_name","value":"test.name"}
    ],
    "select":[
        {
            "name":"d90",
            "aggregate":"percentile",
            "percentile":0.9,
            "value":"result.duration"
        },
        {
            "name":"dtotal",
            "aggregate":"sum",
            "value":"result.duration"
        },
        {
            "name":"count",
            "aggregate":"count"
        },
        {
            "name":"failures",
            "aggregate":"sum",
            "value":{"when":{"eq":{"result.ok":"F"}}, "then":1, "else":0}
        },
        {
            "name":"start",
            "aggregate":"min",
            "value":"run.stats.start_time"
        },
        {
            "name":"end",
            "aggregate":"max",
            "value":"run.stats.end_time"
        }
    ],
    "where":{"and":[
        {"eq":{"run.jenkins_url":"https://fx-test-jenkins.stage.mozaws.net/"}},
        {"gt":{"run.stats.start_time":{"date":"today-4week"}}}
    ]},
    "limit":1000
}"""
    r = requests.post(url, data=query).json()
    return pd.DataFrame(r['data'], columns=r['header'])


def get_lowest_pass_rate(df):
    jobs = get_lowest_pass_rate_jobs(df)
    return [{'job': job, 'tests': get_lowest_pass_rate_tests(df, job)}
            for job in jobs]


def get_lowest_pass_rate_jobs(df, limit=10):
    df = df.groupby(by='job', sort=False).sum()
    df['pass'] = 1 - df['failures']/df['count']  # recalculate pass rate
    return df.sort_values('pass', ascending=True) \
        .reset_index()[:limit]['job'].values


def get_lowest_pass_rate_tests(df, job, limit=10):
    colors = list(Color('red').range_to(Color('lime'), 101))
    tests = df[df['job'] == job] \
        .sort_values('pass', ascending=True)[:limit] \
        .to_dict(orient='records')
    for t in tests:
        pc = t['pass'] * 100
        t['pass'] = {
            'percent': '{0:.0f}%'.format(pc),
            'color': colors[int(pc)].hex}
    return tests


def get_most_failing(df):
    jobs = get_most_failing_jobs(df)
    return [{'job': job, 'tests': get_most_failing_tests(df, job)}
            for job in jobs]


def get_most_failing_jobs(df, limit=10):
    return df.groupby(by='job', sort=False).sum() \
        .sort_values('failures', ascending=False) \
        .reset_index()[:limit]['job'].values


def get_most_failing_tests(df, job, limit=10):
    return df[df['job'] == job] \
        .sort_values('failures', ascending=False)[:limit] \
        .to_dict(orient='records')


def get_slowest(df):
    jobs = get_slowest_jobs(df)
    return [{'job': job, 'tests': get_slowest_tests(df, job)} for job in jobs]


def get_slowest_jobs(df, limit=10):
    return df.groupby(by='job', sort=False).sum() \
        .sort_values('d90', ascending=False) \
        .reset_index()[:limit]['job'].values


def get_slowest_tests(df, job, limit=10):
    df = df[df['job'] == job] \
        .sort_values('d90', ascending=False)[:limit]
    df['duration'] = df['d90'].apply(lambda x: naturaldelta(x))
    return df.to_dict(orient='records')


def get_longest(df):
    jobs = get_longest_jobs(df)
    return [{'job': job, 'tests': get_longest_tests(df, job)} for job in jobs]


def get_longest_jobs(df, limit=10):
    return df.groupby(by='job', sort=False).sum() \
        .sort_values('dtotal', ascending=False) \
        .reset_index()[:limit]['job'].values


def get_longest_tests(df, job, limit=10):
    df = df[df['job'] == job] \
        .sort_values('dtotal', ascending=False)[:limit]
    df['duration'] = df['dtotal'].apply(lambda x: naturaldelta(x))
    return df.to_dict(orient='records')


if __name__ == "__main__":
    df = get_data()
    generated = datetime.now()
    start = datetime.fromtimestamp(df['start'].min())
    end = datetime.fromtimestamp(df['end'].max())
    df['failures'] = df['failures'].astype(int)
    df['pass'] = 1 - df['failures']/df['count']  # calculate pass rate
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    template_vars = {
        'total': '{:,}'.format(df['count'].sum()),
        'start':  start.strftime('%d-%b-%Y'),
        'end': end.strftime('%d-%b-%Y'),
        'generated': {
            'date': generated.strftime('%d-%b-%Y'),
            'time': generated.strftime('%H:%M:%S')},
        'lowest_pass_rate': get_lowest_pass_rate(df),
        'most_failing': get_most_failing(df),
        'slowest': get_slowest(df),
        'longest': get_longest(df)}
    html = template.render(template_vars)
    with open(sys.argv[1], 'w') as f:
        f.writelines(html)
