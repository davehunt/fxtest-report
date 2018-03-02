import os

import pandas as pd
import requests
from colour import Color
from humanize import naturaldelta


class ActiveData(object):

    def __init__(self, use_cache=False):
        self.cache = '.cache'
        if use_cache and not os.path.exists(self.cache):
            os.makedirs(self.cache)
        self.url = 'http://activedata.allizom.org/query'
        self.use_cache = use_cache

    def _get_color(self, value, _max, _min=0):
        spectrum = list(Color('lime').range_to(Color('red'), 100))
        percent = ((value - _min) / (_max - _min)) * 100
        index = int(max(0, min(99, percent)))
        return spectrum[index].hex

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
        if self.use_cache:
            with open(cache_path, 'w') as f:
                df.to_pickle(cache_path)
        return df

    def get_total_durations(self):
        df = self._get_data('total_durations')
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.sort_values('date', inplace=True)
        df.set_index('date', inplace=True)
        return df

    def get_job_durations(self):
        df = self._get_data('job_durations')
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.sort_values(by=['job', 'date'], inplace=True)
        df.set_index(['job', 'date'], inplace=True)
        return df

    def get_test_durations(self):
        df = self._get_data('test_durations')
        df['failures'] = df['failures'].astype(int)
        df['pass'] = 1 - df['failures']/df['count']  # calculate pass rate
        return df

    def get_outcomes(self):
        df = self._get_data('outcomes')
        df['date'] = pd.to_datetime(df['date'], unit='s')
        return df

    def get_lowest_pass_rate(self, df):
        return [{
            'job': j['job'],
            'percent': j['percent'],
            'color': j['color'],
            'tests': self.get_lowest_pass_rate_tests(df, j['job'])}
                for j in self.get_lowest_pass_rate_jobs(df)]

    def get_lowest_pass_rate_jobs(self, df, limit=10):
        jdf = df.groupby(by='job', sort=False).sum()
        jdf['pass'] = 1 - jdf['failures']/jdf['count']  # recalculate pass rate
        df = jdf.sort_values('pass', ascending=True).reset_index()[:limit]
        df['percent'] = df['pass'].apply(lambda x: '{0:.0f}%'.format(x * 100))
        df['color'] = df['pass'].apply(
            lambda x: self._get_color(100 - (x * 100), 20))
        return df.to_dict(orient='records')

    def get_lowest_pass_rate_tests(self, df, job, limit=10):
        df = df[df['job'] == job] \
            .sort_values('pass', ascending=True)[:limit]
        df['percent'] = df['pass'].apply(lambda x: '{0:.0f}%'.format(x * 100))
        df['color'] = df['pass'].apply(
            lambda x: self._get_color(100 - (x * 100), 20))
        return df.to_dict(orient='records')

    def get_most_failing(self, df):
        return [{
            'job': j['job'],
            'failures': j['failures'],
            'color': j['color'],
            'tests': self.get_most_failing_tests(df, j['job'])}
                for j in self.get_most_failing_jobs(df)]

    def get_most_failing_jobs(self, df, limit=10):
        df = df.groupby(by='job', sort=False).sum() \
            .sort_values('failures', ascending=False) \
            .reset_index()[:limit]
        df['color'] = df['failures'].apply(lambda x: self._get_color(x, 500))
        return df.to_dict(orient='records')

    def get_most_failing_tests(self, df, job, limit=10):
        df = df[df['job'] == job] \
            .sort_values('failures', ascending=False)[:limit]
        df['color'] = df['failures'].apply(lambda x: self._get_color(x, 50))
        return df.to_dict(orient='records')

    def get_slowest(self, df):
        return [{
            'job': j['job'],
            'duration': j['duration'],
            'color': j['color'],
            'tests': self.get_slowest_tests(df, j['job'])}
                for j in self.get_slowest_jobs(df)]

    def get_slowest_jobs(self, df, limit=10):
        df = df.groupby(by='job', sort=False).sum() \
            .sort_values('d90', ascending=False) \
            .reset_index()[:limit]
        df['duration'] = df['d90'].apply(lambda x: naturaldelta(x))
        df['color'] = df['d90'].apply(lambda x: self._get_color(x, 1800, 600))
        return df.to_dict(orient='records')

    def get_slowest_tests(self, df, job, limit=10):
        df = df[df['job'] == job] \
            .sort_values('d90', ascending=False)[:limit]
        df['duration'] = df['d90'].apply(lambda x: naturaldelta(x))
        df['color'] = df['d90'].apply(lambda x: self._get_color(x, 90, 30))
        return df.to_dict(orient='records')

    def get_longest(self, df):
        return [{
            'job': j['job'],
            'duration': j['duration'],
            'color': j['color'],
            'tests': self.get_longest_tests(df, j['job'])}
                for j in self.get_longest_jobs(df)]

    def get_longest_jobs(self, df, limit=10):
        df = df.groupby(by='job', sort=False).sum() \
            .sort_values('dtotal', ascending=False) \
            .reset_index()[:limit]
        df['duration'] = df['dtotal'].apply(lambda x: naturaldelta(x))
        df['color'] = df['dtotal'].apply(lambda x: self._get_color(x, 259200))
        return df.to_dict(orient='records')

    def get_longest_tests(self, df, job, limit=10):
        df = df[df['job'] == job] \
            .sort_values('dtotal', ascending=False)[:limit]
        df['duration'] = df['dtotal'].apply(lambda x: naturaldelta(x))
        df['color'] = df['dtotal'].apply(lambda x: self._get_color(x, 10800))
        return df.to_dict(orient='records')
