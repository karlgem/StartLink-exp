# Karl Gemayel
# Georgia Institute of Technology
#
# Created: April 26, 2019

import logging
import argparse

from typing import *

# noinspection All
import pathmagic

# noinspection PyUnresolvedReferences
import sbsp_log  # runs init in sbsp_log and configures logger

import sbsp_argparse.parallelization
import sbsp_argparse.sbsp

from sbsp_general import Environment
from sbsp_options.sbsp import SBSPOptions
from sbsp_options.pbs import PBSOptions
from sbsp_options.pipeline_sbsp import PipelineSBSPOptions


# ------------------------------ #
#           Parse CMD            #
# ------------------------------ #
from sbsp_pipeline.pipeline_msa import PipelineSBSP

parser = argparse.ArgumentParser("Description of driver.")

parser.add_argument('--pf-q-list', required=True, help="File containing names of query genomes")
parser.add_argument('--pf-t-db', required=True, help="(Diamond) Blast database")
parser.add_argument('--pf-output', required=True, help="Output file containing query-target information used by SBSP")

parser.add_argument('--fn-q-labels', default="ncbi.gff", required=False, type=Union[str],
                    help="Name of query file(s) containing gene labels")
parser.add_argument('--fn-t-labels', default="ncbi.gff", required=False, type=Union[str],
                    help="Name of target file(s) containing gene labels")

parser.add_argument("--fn-q-labels-true", default="ncbi.gff", required=False, type=Union[str],
                    help="Name of true labels file. If set, accuracy is computed after MSA.")

parser.add_argument('--steps', nargs="+", required=False,
                    choices=["find-orthologs", "compute-features", "filter", "build-msa", "accuracy"],
                    default=None)

parser.add_argument('--upstream-length-nt', required=False, default=None, type=Union[int],
                    help="The maximum number of upstream nucleotides (from annotation) to use in MSA")
parser.add_argument('--downstream-length-nt', required=False, default=None, type=Union[int],
                    help="The maximum number of downstream nucleotides to use in MSA")

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


def main(env, args):
    # type: (Environment, argparse.Namespace) -> None

    sbsp_options = SBSPOptions.init_from_dict(env, vars(args))
    pbs_options = PBSOptions.init_from_dict(env, vars(args))

    pipeline_options = PipelineSBSPOptions(
        env, **vars(args), sbsp_options=sbsp_options, pbs_options=pbs_options,
    )

    p_sbsp = PipelineSBSP(env, pipeline_options)
    p_sbsp.run()


if __name__ == "__main__":
    main(my_env, parsed_args)
