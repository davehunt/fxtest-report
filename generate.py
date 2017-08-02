import argparse
from datetime import datetime
import os

from jinja2 import Environment, FileSystemLoader

from active_data import ActiveData

import matplotlib
matplotlib.use('Agg')  # force matplotlib to not use any xwindows backend

import matplotlib.dates as dates
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import matplotlib.ticker as ticker
import seaborn as sns

params = {
    'legend.fontsize': 'x-small',
    'axes.labelsize': 'x-small',
    'axes.titlesize': 'x-small',
    'xtick.labelsize': 'x-small',
    'ytick.labelsize': 'x-small',
    'legend.edgecolor': 'grey',
    'legend.fancybox': True,
    'legend.facecolor': 'white'}
pylab.rcParams.update(params)
sns.set_style('darkgrid')


def format_axis(axis):
    axis.legend(loc='upper left', frameon=True).set_title('')
    axis.xaxis.set_major_locator(dates.DayLocator(interval=7))
    axis.xaxis.set_major_formatter(dates.DateFormatter('%d\n%b'))
    axis.xaxis.set_minor_formatter(ticker.NullFormatter())
    axis.set_xlabel('')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate report of Firefox Test Engineering results')
    parser.add_argument('-o', dest='output', default='out',
                        help='path to write the report')
    parser.add_argument('--use-cache', action='store_true',
                        help='use cached results if they exist')
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    ad = ActiveData(use_cache=args.use_cache)
    tddf = ad.get_test_durations()
    generated = datetime.now()
    start = datetime.fromtimestamp(tddf['start'].min())
    end = datetime.fromtimestamp(tddf['end'].max())
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    template_vars = {
        'total': '{:,}'.format(tddf['count'].sum()),
        'start':  start.strftime('%d-%b-%Y'),
        'end': end.strftime('%d-%b-%Y'),
        'generated': {
            'date': generated.strftime('%d-%b-%Y'),
            'time': generated.strftime('%H:%M:%S')},
        'lowest_pass_rate': ad.get_lowest_pass_rate(tddf),
        'most_failing': ad.get_most_failing(tddf),
        'slowest': ad.get_slowest(tddf),
        'longest': ad.get_longest(tddf),
        'jobs': sorted(list(tddf.job.unique()))}

    jddf = ad.get_job_durations()

    o = {'T': 'expected', 'F': 'unexpected'}
    odf = ad.get_outcomes()

    fig, axes = plt.subplots(1, 3, figsize=(15, 2))
    todf = odf.groupby(by=['date', 'ok', 'result'])['count'] \
        .sum().unstack(level=1).unstack()
    for ok, ax in zip(o.keys(), axes[:2]):
        a = todf[ok].plot(ax=ax, title='all jobs ({} outcomes)'.format(o[ok]))
        format_axis(a)

    tddf = ad.get_total_durations()
    a = tddf.plot(ax=axes[2], title='all jobs (durations)')
    format_axis(a)

    fig.savefig(
        os.path.join(args.output, 'total.png'),
        bbox_inches='tight', pad_inches=0)

    jodf = odf.groupby(by=['job', 'date', 'ok', 'result'])['count'] \
        .sum().unstack(level=2).unstack()
    for job in jodf.index.levels[0]:
        fig, axes = plt.subplots(1, 3, figsize=(15, 2))
        for ok, ax in zip(o.keys(), axes[:2]):
            t = '{} ({} outcomes)'.format(job, o[ok])
            a = jodf.loc[job][ok].plot(ax=ax, title=t)
            format_axis(a)
        t = '{} (durations)'.format(job)
        a = jddf.loc[job].plot(ax=axes[2], title=t)
        format_axis(a)
        fig.savefig(
            os.path.join(args.output, '{}.png'.format(job)),
            bbox_inches='tight', pad_inches=0)

    html = template.render(template_vars)
    with open(os.path.join(args.output, 'index.html'), 'w') as f:
        f.writelines(html)
