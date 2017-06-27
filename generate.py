import argparse
from datetime import datetime
import os

from jinja2 import Environment, FileSystemLoader

from active_data import ActiveData

import matplotlib
matplotlib.use('Agg')  # force matplotlib to not use any xwindows backend

import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate report of Firefox Test Engineering results')
    parser.add_argument('-o', dest='output', default='report.html',
                        help='path to write the report')
    parser.add_argument('--use-cache', action='store_true',
                        help='use cached results if they exist')
    args = parser.parse_args()

    ad = ActiveData(use_cache=args.use_cache)
    ddf = ad.get_durations()
    generated = datetime.now()
    start = datetime.fromtimestamp(ddf['start'].min())
    end = datetime.fromtimestamp(ddf['end'].max())
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    template_vars = {
        'total': '{:,}'.format(ddf['count'].sum()),
        'start':  start.strftime('%d-%b-%Y'),
        'end': end.strftime('%d-%b-%Y'),
        'generated': {
            'date': generated.strftime('%d-%b-%Y'),
            'time': generated.strftime('%H:%M:%S')},
        'lowest_pass_rate': ad.get_lowest_pass_rate(ddf),
        'most_failing': ad.get_most_failing(ddf),
        'slowest': ad.get_slowest(ddf),
        'longest': ad.get_longest(ddf)}

    o = {'T': 'expected', 'F': 'unexpected'}
    odf = ad.get_outcomes()
    jodf = odf.groupby(by=['job', 'date', 'ok', 'result'])['count'] \
        .sum().unstack(level=2).unstack()

    jobs = jodf.index.levels[0]
    fig, axes = plt.subplots(len(jobs) + 1, 2, sharex=True, figsize=(10, 40))
    plt.subplots_adjust(hspace=0.3, wspace=0.2)

    todf = odf.groupby(by=['date', 'ok', 'result'])['count'] \
        .sum().unstack(level=1).unstack()

    for ok, ax in zip(o.keys(), axes[0]):
        a = todf[ok].plot(ax=ax, title='all jobs ({} outcomes)'.format(o[ok]))
        a.legend(loc='upper left', frameon=True).set_title('')

    for job, ax in zip(jobs, axes[1:]):
        for ok, ax in zip(o.keys(), ax):
            t = '{} ({} outcomes)'.format(job, o[ok])
            a = jodf.loc[job][ok].plot(ax=ax, title=t)
            a.legend(loc='upper left', frameon=True).set_title('')
            a.set_ylim(ymin=0)
            a.set_xlabel('')

    fig.savefig(
        os.path.join(os.path.dirname(args.output), 'overview.png'),
        bbox_inches='tight', pad_inches=0)

    html = template.render(template_vars)
    with open(args.output, 'w') as f:
        f.writelines(html)
