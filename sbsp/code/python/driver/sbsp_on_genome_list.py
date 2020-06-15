# Karl Gemayel
# Georgia Institute of Technology
#
# Created: 3/17/20
import logging
import random
import threading
import time
import argparse
import pandas as pd
from copy import copy, deepcopy
from typing import *

# noinspection All
import pathmagic

# noinspection PyUnresolvedReferences
import sbsp_log  # runs init in sbsp_log and configures logger

# Custom imports
from sbsp_container.genome_list import GenomeInfoList, GenomeInfo
from sbsp_general import Environment
import sbsp_argparse.parallelization
import sbsp_argparse.sbsp

# ------------------------------ #
#           Parse CMD            #
# ------------------------------ #
from sbsp_general.general import os_join
from sbsp_io.general import mkdir_p
from sbsp_options.parallelization import ParallelizationOptions
from sbsp_options.pipeline_sbsp import PipelineSBSPOptions
from sbsp_options.sbsp import SBSPOptions
from sbsp_pipeline.pipeline_msa import PipelineSBSP

parser = argparse.ArgumentParser("Run SBSP on a list of genomes.")

parser.add_argument('--pf-q-list', required=True, help="File of query genomes")
parser.add_argument('--pf-db-index', required=True, help="Path to file containing database information for each ancestor clade")

parser.add_argument('--simultaneous-genomes', type=int, default=1, help="Number of genomes to run on simultaneously.")
parser.add_argument('--dn-run', default="sbsp", help="Name of directory with SBSP run.")

parser.add_argument('--fn-q-labels', default="ncbi.gff", required=False, type=Union[str],
                    help="Name of query file(s) containing gene labels")
parser.add_argument('--fn-t-labels', default="ncbi.gff", required=False, type=Union[str],
                    help="Name of target file(s) containing gene labels")

parser.add_argument("--fn-q-labels-true", default="ncbi.gff", required=False, type=Union[str],
                    help="Name of true labels file. If set, accuracy is computed after MSA.")

parser.add_argument('--steps', nargs="+", required=False,
                    choices=["prediction", "comparison"],
                    default=None)

sbsp_argparse.parallelization.add_parallelization_options(parser)
sbsp_argparse.sbsp.add_sbsp_options(parser)

# parser.add_argument(
#     f"--pf-parallelization-options", required=False, default=None,
#     help=f"Configuration file for parallelization"
# )


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

def sbsp_on_gi(gi, pipeline_options):
    # type: (GenomeInfo, PipelineSBSPOptions) -> None
    random.seed(1)
    logger.debug("Running for {}".format(gi.name))
    PipelineSBSP(pipeline_options.env, pipeline_options).run()
    logger.debug("Done for {}".format(gi.name))

def get_clade_to_pf_db(pf_db_index):
    # type: (str) -> Dict[str, str]
    df = pd.read_csv(pf_db_index)
    return {
        r["Clade"]: r["pf-db"] for _, r in df.iterrows()
    }

class TransferThread (threading.Thread):
    def __init__(self, env, thread_id, gi, po, lock):
        # type: (Environment, Any, GenomeInfo, PipelineSBSPOptions, threading.Lock) -> None
        threading.Thread.__init__(self)
        self.env = env
        self.thread_id = thread_id
        self.gi = gi
        self.po = po
        self.lock = lock


    def run(self):
        sbsp_on_gi(self.gi, self.po)


def wait_for_all(active_threads):
    # type: (List[threading.Thread]) -> List[threading.Thread]

    done_threads = list()
    while True:
        if len(active_threads) == 0:
            break
        for i, t in enumerate(active_threads):
            if not t.is_alive():
                del active_threads[i]
                done_threads.append(t)

        time.sleep(30)

    return done_threads

def wait_for_any(active_threads):
    # type: (List[threading.Thread]) -> Union[threading.Thread, None]

    while True:
        if len(active_threads) == 0:
            return None
        for i, t in enumerate(active_threads):
            if not t.is_alive():
                del active_threads[i]
                return t

        time.sleep(30)


def main(env, args):
    # type: (Environment, argparse.Namespace) -> None

    gil = GenomeInfoList.init_from_file(args.pf_q_list)
    sbsp_options = SBSPOptions.init_from_dict(env, vars(args))

    prl_options = ParallelizationOptions.init_from_dict(env, vars(args))

    # read database index file
    clade_to_pf_db = get_clade_to_pf_db(args.pf_db_index)


    import multiprocessing as mp
    pool = mp.Pool(processes=args.simultaneous_genomes)

    # create job vector for parallel processing
    job_vector = list()

    lock = threading.Lock()
    active_threads = list()
    thread_id = 0
    for gi in gil:
        logger.info("Scheduling: {}".format(gi.name))
        pd_work = os_join(env["pd-work"], gi.name, args.dn_run)
        curr_env = env.duplicate({"pd-work": pd_work})

        pf_output = os_join(pd_work, "output.csv")

        try:
            pf_t_db = clade_to_pf_db[gi.attributes["ancestor"]]
        except KeyError:
            raise ValueError("Unknown clade {}".format(gi.attributes["ancestor"]))

        po = PipelineSBSPOptions(
            curr_env, **vars(args), pf_t_db=pf_t_db, pf_output=pf_output, sbsp_options=sbsp_options,
            prl_options=prl_options,
        )

        # create working dir

        pf_list = os_join(pd_work, "query.list")
        mkdir_p(pd_work)

        # write genome to local list file
        GenomeInfoList([gi]).to_file(pf_list)

        # update custom options to local gi

        po['pf-q-list'] = pf_list

        thread = TransferThread(env, thread_id, gi, po, lock)
        thread.start()
        thread_id += 1

        active_threads.append(thread)

        # wait until number of active threads is low
        if len(active_threads) >= args.simultaneous_genomes:
            wait_for_any(active_threads)

        time.sleep(5)

    wait_for_all(active_threads)






if __name__ == "__main__":
    main(my_env, parsed_args)
