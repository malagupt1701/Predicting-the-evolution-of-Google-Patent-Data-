import os
import pandas as pd
import time
import boto3
import shutil
from smart_open import open

path_name = 'capstone-storage'

access_key_id  = 'AKIA4DCDKSPQB6DM4TWS'
secret_access_key = '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'

session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
resources = session.resource('s3')

s3 = session.client('s3')
my_bucket = resources.Bucket('capstone-storage')

response = s3.list_objects_v2(Bucket='capstone-storage', Prefix = 'cleaned_data_with_description/2018')
files = response.get("Contents")

allf = []

for file in files:
    if (loc := file['Key']).endswith('.csv'):
        print(f"Retrieving {loc}")
        path = 's3://{}:{}@{}/{}'.format(access_key_id, secret_access_key, path_name, loc)
        allf.append(pd.read_csv(open(path, 'rb', transport_params={'client': s3})))

aggf = pd.concat(allf, axis=0, ignore_index=True)
word_vecs = aggf["Description"].map(
        lambda s: pd.Series(dict(eval(s[11:-1])), dtype="f8"))
word_vecs = word_vecs.to_list()

def chunk_sets(ls, chunk_size=100):
    if len(ls) == 1:
        return ls
    out = []
    start = 0
    for end in range(chunk_size, len(ls)+chunk_size, chunk_size):
        chunk = ls[start:min(end, len(ls))]
        joined = pd.concat(chunk, axis=1)
        # joindex = set()
        # for c in chunk:
        #     joindex = set(c.index.tolist()).union(joindex)
        out.append(joined)
        start = end
    return out

def prune(chunked, low_limit=0.01, high_limit=0.5):
    out = []
    for chunk in chunked:
        chunk = chunk.drop(chunk.index[chunk.count(1) > chunk.shape[1] * high_limit], axis=0)
        chunk = chunk.drop(chunk.index[chunk.count(1) < chunk.shape[1] * low_limit], axis=0)
        out.append(chunk)
    return out

chunked = chunk_sets(word_vecs)
while (len(chunked) > 1):
    chunked = chunk_sets(chunked, chunk_size=2)
    chunked = prune(chunked)

with open("2018_all.pkl", "wb") as f:
    f.write(pickle.dump(chunked[0].fillna(0.0)))
