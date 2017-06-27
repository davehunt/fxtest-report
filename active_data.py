import os

from colour import Color
from humanize import naturaldelta
import pandas as pd
import requests


class ActiveData(object):

    def __init__(self, use_cache=False):
        self.cache = '.cache'
        if not os.path.exists(self.cache):
            os.makedirs(self.cache)
        self.url = 'http://activedata.allizom.org/query'
        self.use_cache = use_cache

    def _get_data(self, query):
        cache_path = os.path.join(self.cache, query)
        if self.use_cache:
            try:
                df = pd.read_pickle(cache_path)
                print('Using cached results in {}.'.format(cache_path))
                return df
            except FileNotFoundError:
                print('No cached results found in {}.'.format(cache_path))
        with open(os.path.join('queries', query + '.json'), 'r') as f:
            r = requests.post(self.url, data=f.read()).json()
            df = pd.DataFrame(r['data'], columns=r['header'])
        with open(cache_path, 'w') as f:
            df.to_pickle(cache_path)
        return df

    def get_durations(self):
        df = self._get_data('durations')
        df['failures'] = df['failures'].astype(int)
        df['pass'] = 1 - df['failures']/df['count']  # calculate pass rate
        return df

    def get_outcomes(self):
        df = self._get_data('outcomes')
        df['date'] = pd.to_datetime(df['date'], unit='s')
        return df

    def get_lowest_pass_rate(self, df):
        return self.get_lowest_pass_rate_jobs(df)

    def get_lowest_pass_rate_jobs(self, df, limit=10):
        colors = list(Color('red').range_to(Color('lime'), 101))
        jdf = df.groupby(by='job', sort=False).sum()
        jdf['pass'] = 1 - jdf['failures']/jdf['count']  # recalculate pass rate
        jobs = jdf.sort_values('pass', ascending=True) \
            .reset_index()[:limit] \
            .to_dict(orient='records')
        for j in jobs:
            pc = j['pass'] * 100
            j['pass'] = {
                'percent': '{0:.0f}%'.format(pc),
                'color': colors[int(pc)].hex}
            j['tests'] = self.get_lowest_pass_rate_tests(df, j['job'])
        return jobs

    def get_lowest_pass_rate_tests(self, df, job, limit=10):
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

    def get_most_failing(self, df):
        return [{
            'job': j['job'],
            'failures': j['failures'],
            'tests': self.get_most_failing_tests(df, j['job'])}
                for j in self.get_most_failing_jobs(df)]

    def get_most_failing_jobs(self, df, limit=10):
        return df.groupby(by='job', sort=False).sum() \
            .sort_values('failures', ascending=False) \
            .reset_index()[:limit] \
            .to_dict(orient='records')

    def get_most_failing_tests(self, df, job, limit=10):
        return df[df['job'] == job] \
            .sort_values('failures', ascending=False)[:limit] \
            .to_dict(orient='records')

    def get_slowest(self, df):
        return [{
            'job': j['job'],
            'duration': j['duration'],
            'tests': self.get_slowest_tests(df, j['job'])}
                for j in self.get_slowest_jobs(df)]

    def get_slowest_jobs(self, df, limit=10):
        df = df.groupby(by='job', sort=False).sum() \
            .sort_values('d90', ascending=False) \
            .reset_index()[:limit]
        df['duration'] = df['d90'].apply(lambda x: naturaldelta(x))
        return df.to_dict(orient='records')

    def get_slowest_tests(self, df, job, limit=10):
        df = df[df['job'] == job] \
            .sort_values('d90', ascending=False)[:limit]
        df['duration'] = df['d90'].apply(lambda x: naturaldelta(x))
        return df.to_dict(orient='records')

    def get_longest(self, df):
        return [{
            'job': j['job'],
            'duration': j['duration'],
            'tests': self.get_longest_tests(df, j['job'])}
                for j in self.get_longest_jobs(df)]

    def get_longest_jobs(self, df, limit=10):
        df = df.groupby(by='job', sort=False).sum() \
            .sort_values('dtotal', ascending=False) \
            .reset_index()[:limit]
        df['duration'] = df['dtotal'].apply(lambda x: naturaldelta(x))
        return df.to_dict(orient='records')

    def get_longest_tests(self, df, job, limit=10):
        df = df[df['job'] == job] \
            .sort_values('dtotal', ascending=False)[:limit]
        df['duration'] = df['dtotal'].apply(lambda x: naturaldelta(x))
        return df.to_dict(orient='records')
