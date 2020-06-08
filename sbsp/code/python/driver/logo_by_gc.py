# Karl Gemayel
# Georgia Institute of Technology
#
# Created: 3/17/20
import logging
import argparse
import math

import pandas as pd
from typing import *
import matplotlib.pyplot as plt
import logomaker as lm

# noinspection All
import pathmagic

# noinspection PyUnresolvedReferences
import sbsp_log  # runs init in sbsp_log and configures logger

# Custom imports
from sbsp_general import Environment

# ------------------------------ #
#           Parse CMD            #
# ------------------------------ #
from sbsp_general.shelf import next_name
from sbsp_io.objects import load_obj

parser = argparse.ArgumentParser("Description of driver.")

parser.add_argument('--pf-data', required=True)

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


def motif_dict_to_df(motif_dict):
    # type: (Dict[str, List[float]]) -> pd.DataFrame

    header = sorted(motif_dict.keys())

    list_entries = list()
    motif_length = len(next(iter(motif_dict.values())))

    for i in range(motif_length):
        entry = {
            x: motif_dict[x][i] for x in header
        }

        list_entries.append(entry)

    return pd.DataFrame(list_entries)

def get_models_by_gc(df, gc_values):
    # type: (pd.DataFrame, List[float]) -> List[pd.DataFrame]

    df.sort_values("GC", inplace=True)

    cpi = 0
    result = list()
    for gc in gc_values:

        while cpi < len(df) and df.at[df.index[cpi], "GC"] < gc:
            cpi += 1

        if cpi >= len(df):
            break

        print(df.at[df.index[cpi], "GC"], df.at[df.index[cpi], "Genome"])
        result.append(motif_dict_to_df(df.at[df.index[cpi], "RBS_MAT"]))

    return result


def main(env, args):
    # type: (Environment, argparse.Namespace) -> None
    df_bac = load_obj(args.pf_data).reset_index()        # type: pd.DataFrame
    df_bac = df_bac[df_bac["GENOME_TYPE"].isin({"group-a"})]
    min_gc = 20
    max_gc = 72

    gc_values = range(min_gc, max_gc, 2)
    models = get_models_by_gc(df_bac, gc_values)

    num_plots = len(models)
    num_rows = int(math.sqrt(num_plots))
    num_cols = math.ceil(num_plots / float(num_rows))

    fig, axes = plt.subplots(num_rows, num_cols, sharex="all", sharey="all")

    model_index = 0
    for r in range(num_rows):
        for c in range(num_cols):
            if model_index >= len(models):
                break

            newmod = lm.transform_matrix(models[model_index], to_type="information", from_type="probability")
            lm.Logo(newmod, ax=axes[r][c])

            axes[r][c].set_ylim(0, 2)
            axes[r][c].set_title(gc_values[model_index])

            model_index += 1

    plt.tight_layout()
    plt.savefig(next_name(env["pd-work"]))
    plt.show()





if __name__ == "__main__":
    main(my_env, parsed_args)
