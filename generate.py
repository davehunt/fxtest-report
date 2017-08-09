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

    schema = 'fx-test'

    if not os.path.exists(os.path.join(args.output, schema)):
        os.makedirs(os.path.join(args.output, schema))

    ad = ActiveData(schema, use_cache=args.use_cache)

    summary = ad.get_summary()
    durations = ad.get_durations()
    durations_by_job = ad.get_durations_by_job()
    durations_by_test = ad.get_durations_by_test()
    failures = ad.get_failures()
    failures_by_job = ad.get_failures_by_job()

    generated = datetime.now()
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(os.path.join('templates', 'report.html'))
    template_vars = {
        'schema': schema,
        'generated': {
            'date': generated.strftime('%d-%b-%Y'),
            'time': generated.strftime('%H:%M:%S')},
        'summary': {
            'distinct': '{:,}'.format(summary.distinct[0]),
            'total': '{:,}'.format(summary.total[0]),
            'start': summary.start[0].strftime('%d-%b-%Y'),
            'end': summary.end[0].strftime('%d-%b-%Y')},
        'lowest_pass_rate': ad.get_lowest_pass_rate(durations_by_test),
        'most_failing': ad.get_most_failing(durations_by_test),
        'slowest': ad.get_slowest(durations_by_test),
        'longest': ad.get_longest(durations_by_test),
        'jobs': list(durations_by_job.index.levels[0])}

    fig, axes = plt.subplots(1, 3, figsize=(15, 2))
    format_axis(durations.distinct.plot(ax=axes[0], title='tests'))
    format_axis(durations.elapsed.plot(ax=axes[1], title='durations'))
    format_axis(failures.plot(ax=axes[2], title='failures'))

    fig.savefig(
        os.path.join(args.output, schema, 'total.png'),
        bbox_inches='tight', pad_inches=0)

    for job in durations_by_job.index.levels[0]:
        fig, axes = plt.subplots(1, 3, figsize=(15, 2))
        t = 'tests ({})'.format(job)
        format_axis(durations_by_job.distinct.loc[job].plot(
            ax=axes[0], title=t))
        t = 'durations ({})'.format(job)
        format_axis(durations_by_job.elapsed.loc[job].plot(
            ax=axes[1], title=t))
        try:
            t = 'failures ({})'.format(job)
            a = failures_by_job.loc[job].plot(ax=axes[2], title=t)
            format_axis(a)
        except KeyError:
            pass
        fig.savefig(
            os.path.join(args.output, schema, '{}.png'.format(job)),
            bbox_inches='tight', pad_inches=0)

    html = template.render(template_vars)
    with open(os.path.join(args.output, schema, 'index.html'), 'w') as f:
        f.writelines(html)

    with open(os.path.join(args.output, 'index.html'), 'w') as f:
        template = env.get_template(os.path.join('templates', 'index.html'))
        f.writelines(template.render())
