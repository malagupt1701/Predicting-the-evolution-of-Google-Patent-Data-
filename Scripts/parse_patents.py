import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords

import argparse

DATA_ROOT_DIR = "~/data/"
stopwords = stopwords.words("english") + [".", "-", ":", "(", ")", ";", ","]

def strip_data_tags(line, to_sub):
    out = line
    for sub, substr in to_sub.items():
        subbed = re.sub(sub, substr, out)
        while subbed != out:
            out = subbed
            subbed = re.sub(sub, substr, out)
    return nltk.word_tokenize(out)

def buffer(data_buffer, out, normalized=True):
    if normalized:
        for token in out:
            if token not in stopwords:
                data_buffer[token] = data_buffer.get(token, 0) + 1
    else:
        out = [o for o in out if o not in stopwords]
        data_buffer.append(out)


def flush(data_file_name, data_buffer, normalized=True):
    with open(data_file_name, "w") as f:
        if normalized:
            for token, count in data_buffer.items():
                f.write("%s %s\n" % (token, count))
        else:
            for line in data_buffer:
                f.write("%s\n" % (" ".join(line)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", default=DATA_ROOT_DIR + "ipa220915/ipa220915.xml",
        dest="infile", help="input file")
    parser.add_argument("-o", "--outfile", default=DATA_ROOT_DIR + "proc/ipa220915_{}",
        dest="outfile", help="file pattern to write to")
    parser.add_argument("--no-normalize", action="store_false", dest="normalize",
        help="don't normalize outputs")
    args =  parser.parse_args()

    new_file = "<!DOCTYPE us-patent-application"
    keep_data = ["<p id=.*/p>"]
    keep_meta = []
    to_sub = {
        r"<p id=\"p-\d+\" num=\"\d+\">(.*?)</p>": r"\1",
        r"<b>(.*?)</b>": r"\1",
        r"<i>(.*?)</i>": r"\1",
        r"<figref idref=\"\w+\">(.*?)</figref>": r"\1",
        r"\b\d+\b": "",
        r"\b\d+\w+\b": "",
        r"\n": "",
    }

    with open(args.infile, "r") as infile:
        counter = 0
        data_buffer = {} if args.normalize else []
        for line in infile:
             if line.startswith(new_file):
                 if len(data_buffer):
                     flush(data_file_name, data_buffer, args.normalize)

                 data_file_name = args.outfile.format(counter)
                 meta_file_name = data_file_name + ".meta"
                 data_buffer = {} if args.normalize else []
                 meta_buffer = []

                 meta_file = open(meta_file_name, "w")

                 counter += 1
                 continue
             for keep in keep_data:
                 if re.match(keep, line):
                     out = strip_data_tags(line.lower(), to_sub)
                     buffer(data_buffer, out, args.normalize)
                 break
             else:
                 print("Skipping " + line)
        if len(data_buffer):
             flush(data_file_name, data_buffer, args.normalize)

if __name__ == "__main__":
    main()
