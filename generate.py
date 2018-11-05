import argparse
import os
from datetime import datetime
import logging
from logging.config import dictConfig

import matplotlib  # noqa

matplotlib.use("Agg")  # noqa force matplotlib to not use any xwindows backend
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Environment, FileSystemLoader

from active_data import ActiveData

# noqa
params = {
    "legend.fontsize": "x-small",
    "axes.labelsize": "x-small",
    "axes.titlesize": "x-small",
    "xtick.labelsize": "x-small",
    "ytick.labelsize": "x-small",
    "legend.edgecolor": "grey",
    "legend.fancybox": True,
    "legend.facecolor": "white",
}
pylab.rcParams.update(params)
sns.set_style("darkgrid")

logger = logging.getLogger(__name__)
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "level": "DEBUG",
            "filename": "generate.log",
        },
    },
    "loggers": {
        "": {"handlers": ["console", "file"], "level": "DEBUG", "propogate": True}
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate report of Firefox Test Engineering results"
    )
    parser.add_argument(
        "-o", dest="output", default="report.html", help="path to write the report"
    )
    parser.add_argument(
        "--use-cache", action="store_true", help="use cached results if they exist"
    )
    args = parser.parse_args()

    ad = ActiveData(use_cache=args.use_cache)
    tddf = ad.get_test_durations()
    generated = datetime.now()
    start = datetime.fromtimestamp(tddf["start"].min())
    end = datetime.fromtimestamp(tddf["end"].max())
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.html")
    template_vars = {
        "total": "{:,}".format(tddf["count"].sum()),
        "start": start.strftime("%d-%b-%Y"),
        "end": end.strftime("%d-%b-%Y"),
        "generated": {
            "date": generated.strftime("%d-%b-%Y"),
            "time": generated.strftime("%H:%M:%S"),
        },
        "lowest_pass_rate": ad.get_lowest_pass_rate(tddf),
        "most_failing": ad.get_most_failing(tddf),
        "slowest": ad.get_slowest(tddf),
        "longest": ad.get_longest(tddf),
    }

    jddf = ad.get_job_durations()

    o = {True: "expected", False: "unexpected"}
    odf = ad.get_outcomes()
    jodf = (
        odf.groupby(by=["job", "date", "ok", "result"])["count"]
        .sum()
        .unstack(level=2)
        .unstack()
    )

    jobs = jodf.index.levels[0]
    fig, axes = plt.subplots(len(jobs) + 1, 3, sharex=True, figsize=(15, 2 * len(jobs)))
    plt.subplots_adjust(hspace=0.2, wspace=0.15)

    todf = (
        odf.groupby(by=["date", "ok", "result"])["count"]
        .sum()
        .unstack(level=1)
        .unstack()
    )

    for ok, ax in zip(o.keys(), axes[0]):
        a = todf[ok].plot(ax=ax, title="all jobs ({} outcomes)".format(o[ok]))
        a.legend(loc="upper left", frameon=True).set_title("")

    for job, ax in zip(jobs, axes[1:]):
        for ok, ax in zip(o.keys(), ax[:2]):
            t = "{} ({} outcomes)".format(job, o[ok])
            a = jodf.loc[job][ok].plot(ax=ax, title=t)
            a.legend(loc="upper left", frameon=True).set_title("")
            a.set_ylim(ymin=0)
            a.set_xlabel("")

    tddf = ad.get_total_durations()
    a = tddf.plot(ax=axes[0][2], title="all jobs (durations)")
    a.legend(loc="upper left", frameon=True).set_title("")
    a.set_xlabel("")

    for job, ax in zip(jobs, axes[1:]):
        t = "{} (durations)".format(job)
        a = jddf.loc[job].plot(ax=ax[2], title=t)
        a.legend(loc="upper left", frameon=True).set_title("")
        a.set_xlabel("")

    fig.savefig(
        os.path.join(os.path.dirname(args.output), "overview.png"),
        bbox_inches="tight",
        pad_inches=0,
    )

    html = template.render(template_vars)
    with open(args.output, "w") as f:
        f.writelines(html)


if __name__ == "__main__":
    dictConfig(logging_config)
    main()
