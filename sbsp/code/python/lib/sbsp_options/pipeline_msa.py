import os
from sbsp_general.general import get_value
import sbsp_options.msa
from sbsp_options.pbs import PBSOptions


class PipelineMSAOptions:

    def __init__(self, env, **kwargs):

        # column names
        self.suffix_coordinates = get_value(kwargs, "suffix_coordinates", None)
        self.suffix_gene_sequence = get_value(kwargs, "suffix_gene_sequence", "gene-sequence")
        self.column_k2p_distance = get_value(kwargs, "k2p_distance", "k2p-distance")
        self.tag_msa = get_value(kwargs, "tag_msa", "msa")

        # pbs options
        self.pbs_options = get_value(kwargs, "pbs_options", PBSOptions(env))

        # directories
        self.dn_msa_output = get_value(kwargs, "dn_msa_output", None)

        # paths to files
        self.pf_orthologs = get_value(kwargs, "pf_orthologs", os.path.join(env["pd-work"], "orthologs.csv"))
        self.pf_features = get_value(kwargs, "pf_features", os.path.join(env["pd-work"], "features.csv"))
        self.pf_filter = get_value(kwargs, "pf_filter", os.path.join(env["pd-work"], "filter.csv"))
        self.pf_msa = get_value(kwargs, "pf_msa", os.path.join(env["pd-work"], "msa.csv"))
        self.pf_accuracy = get_value(kwargs, "pf_accuracy", os.path.join(env["pd-work"], "accuracy.csv"))

        self.pf_q_list = get_value(kwargs, "pf_q_list", None)
        self.pf_t_list = get_value(kwargs, "pf_t_list", None)

        # file names
        self.fn_q_labels = get_value(kwargs, "fn_q_labels", "verified.gff")
        self.fn_t_labels = get_value(kwargs, "fn_t_labels", "ncbi.gff")
        self.fn_q_labels_true = get_value(kwargs, "fn_q_labels_true", None)
        self.suffix_labels = get_value(kwargs, "suffix_labels", "")

        # options
        self.upstream_length_nt = get_value(kwargs, "upstream_length_nt", None)
        self.downstream_length_nt = get_value(kwargs, "downstream_length_nt", None)
        self.steps = get_value(kwargs, "steps", None)
        self.multiple_msa_start_selection_threshold = get_value(kwargs, "multiple_msa_start_selection_thresholds", None)

        self.msa_options = get_value(kwargs, "msa_options",
                                sbsp_options.msa.MSAOptions(env))  # type: sbsp_alg.msaoptions.MSAOptions

    def perform_step(self, step):
        # type: (str) -> bool

        if self.steps is None:
            return True

        return step in self.steps
