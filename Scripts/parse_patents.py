import argparse
import os
import subprocess
import glob

import json
import re
from collections import OrderedDict
from multiprocessing import Pool

import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
import xmltodict

DATA_ROOT_DIR = os.path.join(os.path.expanduser("~"), "data")
stopwords = stopwords.words("english")
stopwords += [".", "-", ":", "(", ")", ";", ",", '"', '“', "and/or", "once", "other", "pat", "patent", "published"]

def always_iterable(obj):
    if isinstance(obj, tuple):
        return list(obj)
    elif not isinstance(obj, list):
        return [obj]
    else:
        return obj

def flush(data_file_name, data_buffer, normalized=True):
    with open(data_file_name, "w") as f:
        if normalized:
            for token, count in data_buffer.items():
                f.write("%s %s\n" % (token, count))
        else:
            for line in data_buffer:
                f.write("%s\n" % (" ".join(line)))

def prepare_directory(infile, do_prepare):
    basename = os.path.basename(infile)[:-4]
    if not os.path.exists(path := os.path.join(DATA_ROOT_DIR, basename)):
        os.mkdir(path)

    parsed_path = os.path.join(os.path.expanduser("~"), "data", basename, "F_")
    if not do_prepare:
        print("Skipping directory processing, run " + awk_script_str + " if not already done")
        return parsed_path

    counter = -1
    out_file = None
    with open(infile, "r") as f:
        for line in f.readlines():
            if line.startswith(r"<?xml"):
                if out_file is not None:
                    out_file.close()
                counter += 1
                out_file = open(parsed_path + str(counter), "w")
            print(line, file=out_file)
    return parsed_path

def extract_text(dico):
    text = []
    for entry in dico["description"]["p"]:
        if "#text" in entry:
            text += nltk.word_tokenize(entry["#text"])

    text += extract_claim_text(dico["claims"]["claim"])
    return text

def extract_metadata(dico):
    meta = {}
    meta["country"] = dico["@country"]
    meta["date_produced"] = dico["@date-produced"]
    meta["date_published"] = dico["@date-publ"]
    meta["date_applied"] = dico["us-bibliographic-data-application"]["application-reference"]["document-id"]["date"]
    meta["date_priority"] = always_iterable(
        dico["us-bibliographic-data-application"]
        .get("priority-claims", {}).get("priority-claim", {}))[0].get("date", str(pd.Timestamp(np.nan)))
    meta["country_priority"] = (
        always_iterable(
            dico["us-bibliographic-data-application"]
           .get("priority-claims", {}).get("priority-claim", {})
        )[0].get("country", None)
    )
    biblio = dico["us-bibliographic-data-application"]["us-parties"]
    meta["applicant"] = {
        "orgname": biblio["us-applicants"]["us-applicant"]["addressbook"].get("orgname", None),
        "country": biblio["us-applicants"]["us-applicant"]["addressbook"]["address"]["country"],
        "city": biblio["us-applicants"]["us-applicant"]["addressbook"]["address"]["country"],
    }
    meta["inventor"] = {
        "name": [
             entry["addressbook"]["first-name"] + "|" + entry["addressbook"]["last-name"]
             for entry in always_iterable(biblio["inventors"]["inventor"])
        ],
        "country": [
             entry["addressbook"]["address"]["country"]
             for entry in always_iterable(biblio["inventors"]["inventor"])
        ],
        "city": [
             entry["addressbook"]["address"]["city"]
             for entry in always_iterable(biblio["inventors"]["inventor"])
        ],
    }
    return meta

def extract_claim_text(dico):
    text = []
    def _extract_claim_text(d, collector):
        if isinstance(d, list):
            for dd in d:
                if isinstance(dd, str):
                    collector += nltk.word_tokenize(dd)
                else:
                    _extract_claim_text(dd, collector)
        elif isinstance(d, OrderedDict):
            if "claim-text" in d:
                _extract_claim_text(d["claim-text"], collector)
        return collector
    return _extract_claim_text(dico, text)

def process_all(file_pattern, args, num_threads=1):
    tasks = {}
    for file_i in glob.glob(file_pattern + "*"):
        nid = file_i.split("_")[-1]
        with open(file_i, "r") as f:
            dico = xmltodict.parse(f.read())["us-patent-application"]
        tasks[nid] = (nid, dico, args)

    if num_threads == 1:
        [process_one_file(*tasks[nid]) for nid in tasks]
    else:
        p = Pool(num_threads)
        p.map(process_one_file, tasks)

def process_one_file(nid, dico, args):
    global stopwords

    meta = extract_metadata(dico)

    text = [token for token in extract_text(dico) if token not in stopwords]
    if args.normalize:
        text = np.array(text)
        text, counts = np.unique(text, return_counts=True)
        text = dict(zip(text, counts))

    data_file_name = args.outfile.format(nid)
    flush(data_file_name, text, args.normalize)
    with open(data_file_name + ".meta", "w") as f:
        f.write(json.dumps(meta, indent=4, sort_keys=True))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", default=os.path.join(DATA_ROOT_DIR, "ipa220915.xml"),
        dest="infile", help="input file")
    parser.add_argument("-o", "--outfile", default=os.path.join(DATA_ROOT_DIR, "ipa220915/ipa220915_{}"),
        dest="outfile", help="file pattern to write to")
    parser.add_argument("-t", "--threads", type=int, default=1,
        dest="threads", help="number of threads to use")
    parser.add_argument("--no-normalize", action="store_false", dest="normalize",
        help="don't normalize outputs")
    parser.add_argument("--prepare-directory", action="store_false", dest="prepare_directory",
        help="do prepare directory (otherwise assumed already prepared)")
    args =  parser.parse_args()

    file_pattern = prepare_directory(args.infile, args.prepare_directory)
    process_all(file_pattern, args, min(args.threads, 32))


if __name__ == "__main__":
    main()
