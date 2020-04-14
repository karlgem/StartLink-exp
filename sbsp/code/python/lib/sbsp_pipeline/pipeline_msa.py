import os
import timeit
from shutil import copyfile
from typing import *

from sbsp_alg.sbsp_steps import sbsp_step_accuracy, sbsp_steps
from sbsp_general import Environment
from sbsp_io.general import read_rows_to_list
from sbsp_options.pipeline_sbsp import PipelineSBSPOptions


class PipelineSBSP:

    class PipelineState:
        def __init__(self, list_pf_data):
            self.use_pbs = True  # FIXME: allow non-pbs option
            self.list_pf_data = list_pf_data

            self._only_keep_files_that_exist()

        def _only_keep_files_that_exist(self):
            # type: () -> ()
            self.list_pf_data = [curr for curr in self.list_pf_data if os.path.exists(curr)]

        @classmethod
        def from_file(cls, pf_list_pf_data):
            # type: (str) -> PipelineSBSP.PipelineState

            list_pf_data = read_rows_to_list(pf_list_pf_data)
            return cls(list_pf_data)

    def __init__(self, env, pipeline_options, **kwargs):
        # type: (Environment, PipelineSBSPOptions, Dict[str, Any]) -> None

        self.env = env
        self.pipeline_options = pipeline_options

    def run(self):
        # type: () -> None

        elapsed_times = dict()

        # Copy Information file to local directory
        copyfile(self.pipeline_options["pf-q-list"], os.path.join(self.env["pd-work"], "query.list"))

        curr_time = timeit.default_timer()
        state = self._run_helper()
        elapsed_times["1-compute-steps"] = timeit.default_timer() - curr_time

        curr_time = timeit.default_timer()
        self._accuracy(state)
        elapsed_times["2-accuracy"] = timeit.default_timer() - curr_time

        time_string = "\n".join([
                "{},{}".format(key, value) for key, value in elapsed_times.items()
        ])

        pf_time = os.path.join(self.env["pd-work"], "time.csv")
        with open(pf_time, "w") as f:
            f.write(time_string)
            f.close()

    def _accuracy(self, state):
        # type: (PipelineState) -> PipelineState
        curr_env = self.env.duplicate({
            "pd-work": os.path.join(self.env["pd-work"], "accuracy")
        })
        result = sbsp_step_accuracy(curr_env, self.pipeline_options, state.list_pf_data)

        return PipelineSBSP.PipelineState(result)

    def _run_helper(self, ):
        # type: () -> PipelineState
        curr_env = self.env.duplicate({
            "pd-work": os.path.join(self.env["pd-work"], "steps")
        })
        result = sbsp_steps(curr_env, self.pipeline_options)

        return PipelineSBSP.PipelineState(result)
