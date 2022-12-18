import os
import pandas as pd
import numpy as np
import glob

files = {}
for fn in glob.glob("/Users/sanjeevtewani/Downloads/*-merged.csv"):
    key = int(os.path.basename(fn).replace("-merged.csv", ""))
    files[key] = pd.read_csv(fn, parse_dates=["App_Date"])
files = pd.concat(files, axis=0)
files = files.rename_axis(["file_year", "Unnamed: 0.2"]).reset_index().drop(["Unnamed: 0", "Unnamed: 0.1", "Unnamed: 0.2"], axis=1)
files["pub_ts"] = files["file_year"].map(lambda i: pd.Timestamp(f"{i}-{12-2*(i == 2022):02.0f}-31")).sort_values()

# remove lines where the lag is too long to make sense -- 2.5 years or 913 days
mask = ((files["pub_ts"] - files["App_Date"]) < pd.Timedelta(days=913))
files = files[mask]

def compute_seasonal_profile(tbl, since, to):
    seasonal_adj = tbl.divide(tbl.mean(1), axis=0).mean(0)
    seasonal_adj /= seasonal_adj.mean()

    return seasonal_adj

def seasonal_adj_series(data, key, since, to, agg_fun="count"):
    agg = pd.Index(data[key].sort_values()).to_series().resample("M").count()

    tbl = agg.loc[since:to].rename(lambda t: (t.year, t.month))
    tbl.index = pd.MultiIndex.from_tuples(tbl.index)

    agg = agg.rename(lambda t: (t.year, t.month))
    agg.index = pd.MultiIndex.from_tuples(agg.index)

    tbl = tbl.unstack()

    seasonal_adj = compute_seasonal_profile(tbl, since, to).T
    adj = agg.divide(seasonal_adj, axis=0, level=1)
    adj.index = pd.DatetimeIndex(adj.index.map(lambda s: datetime.date(s[0], s[1], 1)))
    return adj


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

seasonal_adj_series(files, "App_Date", "2017-09", "2020-02").loc["2017-07": "2021-04"].plot()
plt.savefig("seasonally_adjusted_patent_apps")
