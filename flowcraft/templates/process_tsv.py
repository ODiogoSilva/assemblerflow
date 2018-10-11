#!/usr/bin/env python3

import json
import csv
import os

from flowcraft_utils.flowcraft_base import get_logger, MainWrapper

"""
Purpose
-------

This module is intended to process the output in tsv
 to generate a report in json format.


Expected input
--------------

The following variables are expected whether using NextFlow or the
:py:func:`main` executor.

- ``sample_id`` : Sample Identification string.
- ``tsv``: tsv output.

Generated output
----------------
- ``.report.jason``: Data structure for the report

Code documentation
------------------

"""

__version__ = "1.0.1"
__build__ = "05.10.2018"
__template__ = "maxbin2-nf"

logger = get_logger(__file__)

if __file__.endswith(".command.sh"):
    SAMPLE_ID = '$sample_id'
    FILE = '$tsv'
    logger.debug("Running {} with parameters:".format(
        os.path.basename(__file__)))
    logger.debug("SAMPLE_ID: {}".format(SAMPLE_ID))
    logger.debug("FILE: {}".format(FILE))


def main(sample_id, tsv_file):

    with open(".report.json", "w") as k:
        k.write('{"tsvData":[{"sample":"' + sample_id + '", "data": { "MaxBin2":')
        k.write(json.dumps(list(csv.reader(open(tsv_file), delimiter='\t'))))
        k.write('}}]}')


if __name__ == "__main__":
    main(SAMPLE_ID, FILE)

