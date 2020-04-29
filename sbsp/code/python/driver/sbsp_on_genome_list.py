# Karl Gemayel
# Georgia Institute of Technology
#
# Created: 3/17/20
import logging
import argparse
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
from sbsp_options.pbs import PBSOptions
from sbsp_options.pipeline_sbsp import PipelineSBSPOptions
from sbsp_options.sbsp import SBSPOptions
from sbsp_pipeline.pipeline_msa import PipelineSBSP

parser = argparse.ArgumentParser("Description of driver.")

parser.add_argument('--pf-q-list', required=True, help="File of query genomes")
parser.add_argument('--simultaneous-genomes', type=int, default=1, help="Number of genomes to run on simultaneously.")
parser.add_argument('--dn-run', default="sbsp", help="Name of directory with SBSP run")

parser.add_argument('--fn-q-labels', default="ncbi.gff", required=False, type=Union[str],
                    help="Name of query file(s) containing gene labels")
parser.add_argument('--fn-t-labels', default="ncbi.gff", required=False, type=Union[str],
                    help="Name of target file(s) containing gene labels")

parser.add_argument("--fn-q-labels-true", default="ncbi.gff", required=False, type=Union[str],
                    help="Name of true labels file. If set, accuracy is computed after MSA.")

parser.add_argument('--steps', nargs="+", required=False,
                    choices=["find-orthologs", "compute-features", "filter", "build-msa", "accuracy"],
                    default=None)

sbsp_argparse.parallelization.add_pbs_options(parser)
sbsp_argparse.sbsp.add_sbsp_options(parser)

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
    PipelineSBSP(pipeline_options.env, pipeline_options).run()

def main(env, args):
    # type: (Environment, argparse.Namespace) -> None

    gil = GenomeInfoList.init_from_file(args.pf_q_list)
    sbsp_options = SBSPOptions.init_from_dict(env, vars(args))
    pbs_options = PBSOptions.init_from_dict(env, vars(args))

    pipeline_options = PipelineSBSPOptions(
        env, **vars(args), sbsp_options=sbsp_options, pbs_options=pbs_options,
    )


    import multiprocessing as mp
    pool = mp.Pool(processes=args.simultaneous_genomes)

    # create job vector for parallel processing
    job_vector = list()
    for gi in gil:
        po = deepcopy(pipeline_options)

        # create working dir
        pd_work = os_join(po.env["pd-work"], gi.name, args.dn_run)
        pf_list = os_join(pd_work, "query.list")
        mkdir_p(pd_work)

        # write genome to local list file
        GenomeInfoList([gi]).to_file(pf_list)

        # update custom options to local gi
        po.env = po.env.duplicate({"pd-work": pd_work})
        po['pf-q-list'] = pf_list

        pool.apply_async(sbsp_on_gi, args=[gi, po])


    num_jobs = len(job_vector)
    done = 0

    # run jobs
    for p in job_vector:
        p.get()
        logger.info(f"Done {done}/{num_jobs}")



if __name__ == "__main__":
    main(my_env, parsed_args)