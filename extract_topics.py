import pickle
import pandas as pd

import sklearn
from sklearn.decomposition import NMF

year = "2019"
save_filename = year + "_all.pkl"

data = pd.read_csv(year + "-data-merged.csv", index_col=[0])

def get_word_vecs(aggf):
    word_vecs = aggf["Description"].map(
            lambda s: pd.Series(dict(eval(s[11:-1])), dtype="f8"))
    word_vecs = word_vecs.to_list()
    return word_vecs

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

def prune(chunked, low_limit=0.01, high_limit=0.7):
    out = []
    for chunk in chunked:
        chunk = chunk.drop(chunk.index[chunk.count(1) > chunk.shape[1] * high_limit], axis=0)
        chunk = chunk.drop(chunk.index[chunk.count(1) < chunk.shape[1] * low_limit], axis=0)
        out.append(chunk)
    return out

def chunk_and_prune(word_vecs, save_filename=None):
    print(f"Setting up chunk+prune...")
    chunked = chunk_sets(word_vecs)
    full_size = len(chunked)
    print(f"Chunking, {int((1 - len(chunked) / full_size) * 100)}% complete")
    while (len(chunked) > 1):
        chunked = chunk_sets(chunked, chunk_size=2)
        chunked = prune(chunked)
        print(f"Chunking, {int((1 - (len(chunked) - 1) / full_size) * 100)}% complete")

    if save_filename is not None:
        print("Writing to file")
        with open(save_filename, "wb") as f:
            pickle.dump(chunked[0].fillna(0.0), f)
    return chunked[0].fillna(0.0)

def extract_topics(word_mat, ncomp=8, nwords=15, strict_separation=False):
    deco = NMF(n_components=ncomp, init="nndsvd").fit(word_mat.T)
    topics = pd.DataFrame(deco.components_.T, index=word_mat.index)

    if strict_separation:
        # stop words, uninteresting 
        topics = topics.drop(topics.sum(1).sort_values().tail(nwords).index, axis=0)
        topics.where(topics > topics.replace(0.0, np.nan).quantile(0.25), np.nan, inplace=True)

        final = pd.DataFrame()
        for n, top in topics.T.iterrows():
            final[n] = top.drop(final.values.flatten(), axis=0).sort_values().tail(nwords).index

        return final
    return topics

word_vecs = get_word_vecs(data)
word_mat = chunk_and_prune(word_vecs, save_filename)
tops = extract_topics(word_mat, strict_separation=True)
print(tops)
