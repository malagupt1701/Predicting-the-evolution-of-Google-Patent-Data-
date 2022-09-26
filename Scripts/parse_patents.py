import pandas as pd
import numpy as np

import re

import argparse

DATA_ROOT_DIR = "/home/sanjeevt/data/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", default=DATA_ROOT_DIR + "ipa220915/ipa220915.xml", dest="infile")
    parser.add_argument("-o", "--outfile", default=DATA_ROOT_DIR + "proc/ipa220915_{}", dest="outfile")
    args =  parser.parse_args()


    new_file = "<!DOCTYPE us-patent-application"
    to_keep = ["<p id=.*/p>"]
    to_sub = {
        r"<p id=\"p-\d+\" num=\"\d+\">(.*)</p>": r"\1",
        r"<b>(.*)</b>": r"\1",
        r"<i>(.*)</i>": r"\1",
        r"<figref idref=\"\w+\">(.*)</figref>": r"\1",
        r"\n": "",
    }

    with open(args.infile, "r") as infile:
        counter = 0
        while counter < 10:
             line = infile.readline()
             if line.startswith(new_file):
                 filename = args.outfile.format(counter)
                 outfile = open(filename, "w")

                 counter += 1
                 continue
             for keep in to_keep:
                 if re.match(keep, line):
                     out = line
                     for sub, substr in to_sub.items():
                         out = re.sub(sub, substr, out)
                     print(out, file=outfile)
                 break
             else:
                 print("Skipping " + line)


if __name__ == "__main__":
    main()
