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
    summary = ad.get_summary()
    jobs = ad.get_jobs()
    tddf = ad.get_test_durations()
    generated = datetime.now()
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    template_vars = {
        'generated': {
            'date': generated.strftime('%d-%b-%Y'),
            'time': generated.strftime('%H:%M:%S')},
        'summary': {
            'distinct': '{:,}'.format(summary.distinct[0]),
            'total': '{:,}'.format(summary.total[0]),
            'start': summary.start[0].strftime('%d-%b-%Y'),
            'end': summary.end[0].strftime('%d-%b-%Y')},
        'lowest_pass_rate': ad.get_lowest_pass_rate(tddf),
        'most_failing': ad.get_most_failing(tddf),
        'slowest': ad.get_slowest(tddf),
        'longest': ad.get_longest(tddf),
        'jobs': list(jobs.index.levels[0])}

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

    failures_by_job = ad.get_failures_by_job()

    for job in jobs.index.levels[0]:
        fig, axes = plt.subplots(1, 3, figsize=(15, 2))
        t = '{} (tests)'.format(job)
        a = jobs.distinct.loc[job].plot(ax=axes[0], title=t)
        format_axis(a)
        t = '{} (durations)'.format(job)
        a = jobs.elapsed.loc[job].plot(ax=axes[1], title=t)
        format_axis(a)
        try:
            t = '{} (failures)'.format(job)
            a = failures_by_job.loc[job].plot(ax=axes[2], title=t)
            format_axis(a)
        except KeyError:
            pass
        fig.savefig(
            os.path.join(args.output, '{}.png'.format(job)),
            bbox_inches='tight', pad_inches=0)

    html = template.render(template_vars)
    with open(os.path.join(args.output, 'index.html'), 'w') as f:
        f.writelines(html)
