import os
import logging
import numpy as np
import pandas as pd
from typing import *

from Bio.SubsMat import MatrixInfo as matlist

from sbsp_alg.phylogeny import global_alignment_aa_with_gap, k2p_distance
from sbsp_general.general import get_value
from sbsp_io.general import mkdir_p
from sbsp_general import Environment
from sbsp_alg.gene_distances import *


log = logging.getLogger(__name__)



def compute_distance(distance_type, q_align_aa, t_align_aa, q_align_nt, t_align_nt, on_fail=100.0, **kwargs):
    # type: (str, str, str, str, str, float, Dict[str, Any]) -> float

    try:
        if distance_type == "kimura":
            return k2p_distance(q_align_nt, t_align_nt, kimura_on_3rd=False)
        if distance_type == "kimura-on-3rd" or distance_type == "kimura3":
            return k2p_distance(q_align_nt, t_align_nt, kimura_on_3rd=True)

        if distance_type == "ds":
            return compute_distance_ds(q_align_nt, t_align_nt, **kwargs)

        if distance_type == "dn":
            return compute_distance_dn(q_align_nt, t_align_nt, **kwargs)

        if distance_type == "mismatch-aa":
            return compute_distance_mismatch_aa(q_align_aa, t_align_aa, **kwargs)

        if distance_type == "syn-fraction":
            return compute_synonymous_fraction(q_align_aa, t_align_aa, q_align_nt, t_align_nt)

        if distance_type == "non-syn-fraction":
            return compute_non_synonymous_fraction(q_align_aa, t_align_aa, q_align_nt, t_align_nt)

        if distance_type == "syn-poisson":
            return compute_synonymous_poisson(q_align_aa, t_align_aa, q_align_nt, t_align_nt)

        if distance_type == "non-syn-poisson":
            return compute_non_synonymous_poisson(q_align_aa, t_align_aa, q_align_nt, t_align_nt)

    except ValueError:
        return on_fail

    raise ValueError("Unknown distance type: {}".format(distance_type))



def count_aa_mismatches(seq_a, seq_b):
    if len(seq_a) != len(seq_b):
        raise ValueError("Sequence sizes are not the same: {} != {}".format(len(seq_a), len(seq_b)))

    from math import log, sqrt

    alignment_length = len(seq_a)

    matches = 0

    ungapped_length = 0

    for i in range(alignment_length):

        # ignore gaps
        if seq_a[i] == "-" or seq_b[i] == "-":
            continue

        ungapped_length += 1

        if seq_a[i] == seq_b[i]:
            matches += 1

    if ungapped_length == 0:
        return 0.0

    return matches / float(ungapped_length)

def compute_feature_helper(pf_data, **kwargs):
    # type: (str, Dict[str, Any]) -> pd.DataFrame
    # assumes sequences extracted

    df = pd.read_csv(pf_data, header=0)

    suffix_gene_sequence = get_value(kwargs, "suffix_gene_sequence", "gene-sequence")
    column_output = get_value(kwargs, "column_output", "k2p-distance")
    kimura_on_3rd = get_value(kwargs, "kimura_on_3rd", False)
    distance_types = get_value(kwargs, "distance_types", {"kimura"})

    matrix = matlist.blosum62
    import sbsp_alg.phylogeny
    from sbsp_alg.msa import add_gaps_to_nt_based_on_aa
    sbsp_alg.phylogeny.add_stop_codon_to_blosum(matrix)

    df[column_output] = np.nan
    df["aa-match-fraction"] = np.nan

    for index, row in df.iterrows():
        # perform alignment of sequences
        q_sequence = row["q-prot-{}".format(suffix_gene_sequence)]
        t_sequence = row["t-prot-{}".format(suffix_gene_sequence)]

        q_sequence_nt = row["q-nucl-{}".format(suffix_gene_sequence)]
        t_sequence_nt = row["t-nucl-{}".format(suffix_gene_sequence)]

        [q_align, t_align, _, _, _] = \
            global_alignment_aa_with_gap(q_sequence, t_sequence, matrix)

        q_align_nt = add_gaps_to_nt_based_on_aa(q_sequence_nt, q_align)
        t_align_nt = add_gaps_to_nt_based_on_aa(t_sequence_nt, t_align)

        match_aa_frac = count_aa_mismatches(q_align, t_align)

        df.at[index, "aa-match-fraction"] = match_aa_frac

        try:
            df.at[index, column_output] = k2p_distance(q_align_nt, t_align_nt, kimura_on_3rd=kimura_on_3rd)
        except ValueError:
            df.at[index, column_output] = 100

        try:
            df.at[index, "kimura3"] = k2p_distance(q_align_nt, t_align_nt, kimura_on_3rd=True)
        except ValueError:
            df.at[index, "kimura3"] = 100

        for distance_type in distance_types:
            try:
                df.at[index, distance_type] = compute_distance(
                    distance_type,
                    q_align, t_align,
                    q_align_nt, t_align_nt,
                    on_fail=100,
                    **kwargs
                )
            except ValueError:
                df.at[index, distance_type] = 100

    return df

def compute_features(env, pf_data, pf_output, **kwargs):
    # type: (Environment, str, str, Dict[str, Any]) -> str

    pd_work = env["pd-work"]

    mkdir_p(pd_work)

    df = compute_feature_helper(pf_data)

    df.to_csv(pf_output, index=False)
    return pf_output
