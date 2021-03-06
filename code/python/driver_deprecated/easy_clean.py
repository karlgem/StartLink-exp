# Karl Gemayel
# Georgia Institute of Technology
#
# Created: 3/19/20

import logging
import argparse
import pandas as pd
from typing import *

# noinspection All
import pathmagic

# noinspection PyUnresolvedReferences
import sbsp_log  # runs init in sbsp_log and configures logger

# Custom imports
from sbsp_general import Environment

# ------------------------------ #
#           Parse CMD            #
# ------------------------------ #

parser = argparse.ArgumentParser("Description of driver.")

parser.add_argument('--pf-input', required=True)
parser.add_argument('--pf-output', required=True)

parser.add_argument('--pd-work', required=False, default=None, help="Path to working directory")
parser.add_argument('--pd-data', required=False, default=None, help="Path to data directory")
parser.add_argument('--pd-results', required=False, default=None, help="Path to results directory")
parser.add_argument("-l", "--log", dest="loglevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    help="Set the logging level", default='WARNING')

parsed_args = parser.parse_args()

# ------------------------------ #
#           Main Code            #
# ------------------------------ #

# Load environment variables
my_env = Environment(pd_data=parsed_args.pd_data,
                     pd_work=parsed_args.pd_work,
                     pd_results=parsed_args.pd_results)

# Setup logger
logging.basicConfig(level=parsed_args.loglevel)
logger = logging.getLogger("logger")  # type: logging.Logger


def main(env, args):
    # type: (Environment, argparse.Namespace) -> None
    df = pd.read_csv(args.pf_input, header=0)
    df.drop(["q-lorf_nt", "t-lorf_nt"], inplace=True)
    df.to_csv(args.pf_output, index=False)


if __name__ == "__main__":
    main(my_env, parsed_args)
