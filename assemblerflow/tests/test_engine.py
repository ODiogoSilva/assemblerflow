import os
import pytest

import assemblerflow.generator.engine as eg
import assemblerflow.generator.process as pc
import assemblerflow.generator.error_handling as eh

from assemblerflow.generator.engine import process_map


@pytest.fixture
def single_con():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "integrity_coverage", "lane": 1}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "fastqc", "lane": 1}}
           ]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def single_status():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "spades", "lane": 1}}]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def single_con_fasta():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "abricate", "lane": 1}}]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def single_con_multi_raw():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "assembly_mapping", "lane": 1}},
           {"input": {"process": "assembly_mapping", "lane": 1},
            "output": {"process": "pilon", "lane": 1}}]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def implicit_link():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "integrity_coverage", "lane": 1}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "fastqc", "lane": 1}},
           {"input": {"process": "fastqc", "lane": 1},
            "output": {"process": "spades", "lane": 1}},
           {"input": {"process": "spades", "lane": 1},
            "output": {"process": "assembly_mapping", "lane": 1}}]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def implicit_link_2():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "integrity_coverage", "lane": 1}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "spades", "lane": 1}},
           {"input": {"process": "spades", "lane": 1},
            "output": {"process": "assembly_mapping", "lane": 1}}]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def single_fork():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "integrity_coverage", "lane": 1}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "spades", "lane": 2}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "skesa", "lane": 3}}]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def raw_forks():

    con = [{"input": {"process": "__init__", "lane": 0},
            "output": {"process": "integrity_coverage", "lane": 1}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "fastqc", "lane": 1}},
           {"input": {"process": "__init__", "lane": 0},
            "output": {"process": "patho_typing", "lane": 2}},
           {"input": {"process": "__init__", "lane": 0},
            "output": {"process": "seq_typing", "lane": 3}}]

    return eg.NextflowGenerator(con, "teste.nf")


@pytest.fixture
def multi_forks():

    con = [{"input": {"process": "__init__", "lane": 0},
            "output": {"process": "integrity_coverage", "lane": 1}},
           {"input": {"process": "__init__", "lane": 0},
            "output": {"process": "seq_typing", "lane": 2}},
           {"input": {"process": "__init__", "lane": 0},
            "output": {"process": "trimmomatic", "lane": 3}},
           {"input": {"process": "trimmomatic", "lane": 3},
            "output": {"process": "check_coverage", "lane": 3}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "spades", "lane": 4}},
           {"input": {"process": "integrity_coverage", "lane": 1},
            "output": {"process": "skesa", "lane": 5}},
           {"input": {"process": "check_coverage", "lane": 3},
            "output": {"process": "spades", "lane": 6}},
           {"input": {"process": "check_coverage", "lane": 3},
            "output": {"process": "skesa", "lane": 7}}]

    return eg.NextflowGenerator(con, "teste.nf")


def test_simple_init():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "{}", "lane": 1}}]

    for p in process_map:

        con[0]["output"]["process"] = p
        nf = eg.NextflowGenerator(con, "teste/teste.nf")

        assert [len(nf.processes), nf.processes[1].template] == \
            [2, p]


def test_invalid_process():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "invalid", "lane": 1}}]

    with pytest.raises(SystemExit):
        eg.NextflowGenerator(con, "teste.nf")


def test_connections_single_process_channels(single_con):

    template = "integrity_coverage"

    p = single_con.processes[1]

    assert [p.input_channel, p.output_channel] == \
        ["{}_in_1_0".format(template), "{}_out_1_0".format(template)]


def test_connections_invalid():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "spades", "lane": 1}},
           {"input": {"process": "spades", "lane": 1},
            "output": {"process": "integrity_coverage", "lane": 1}}
           ]

    with pytest.raises(SystemExit):
        eg.NextflowGenerator(con, "teste.nf")


def test_connections_ignore_type():

    con = [{"input": {"process": "__init__", "lane": 1},
            "output": {"process": "spades", "lane": 1}},
           {"input": {"process": "spades", "lane": 1},
            "output": {"process": "patho_typing", "lane": 1}}
           ]

    eg.NextflowGenerator(con, "teste.nf")


def test_build_header(single_con):

    single_con._build_header()

    assert single_con.template != ""


def test_connections_nofork(single_con):

    assert single_con._fork_tree == {}


def test_connections_singlefork(single_fork):

    assert single_fork._fork_tree == {1: [2, 3]}


def test_connections_rawfork(raw_forks):

    assert raw_forks._fork_tree == {0: [1, 2, 3]}


def test_connections_multiforks(multi_forks):

    assert multi_forks._fork_tree == {0: [1, 2, 3], 1: [4, 5], 3: [6, 7]}


def test_connections_no_fork_channel_update(single_con):

    p = single_con.processes[1]

    assert p.forks == []


def test_connections_fork_channel_update(single_fork):

    p = single_fork.processes[1]

    assert p.forks != []


def test_connections_channel_update(single_con):

    p1 = single_con.processes[1]
    p2 = single_con.processes[2]

    assert p1.output_channel == p2.input_channel


def test_connections_channel_update_wfork(single_fork):

    p1 = single_fork.processes[1]
    p2 = single_fork.processes[2]
    p3 = single_fork.processes[3]

    assert [p1.main_forks[1], p1.main_forks[2]] == \
           [p2.input_channel, p3.input_channel]


def test_set_channels_single_con_raw_fastq(single_con):

    single_con._set_channels()

    assert [list(single_con.main_raw_inputs.keys())[0],
            len(single_con.main_raw_inputs),
            list(single_con.main_raw_inputs.values())[0]["raw_forks"]] == \
           ["fastq", 1, ["integrity_coverage_in_1_0"]]


def test_set_channels_single_con_raw_fasta(single_con_fasta):

    single_con_fasta._set_channels()

    assert [list(single_con_fasta.main_raw_inputs.keys())[0],
            len(single_con_fasta.main_raw_inputs),
            list(single_con_fasta.main_raw_inputs.values())[0][
                "raw_forks"]] == \
           ["fasta", 1, ["abricate_in_1_0"]]


def test_set_channels_multi_raw_input(single_con_multi_raw):

    single_con_multi_raw._set_channels()

    print(single_con_multi_raw.main_raw_inputs)

    assert [list(single_con_multi_raw.main_raw_inputs.keys()),
            len(single_con_multi_raw.main_raw_inputs)] == \
           [["fasta", "fastq"], 2]


def test_set_channels_secondary_inputs(single_con):

    single_con._set_channels()

    assert list(single_con.secondary_inputs.keys()) == \
        ["genomeSize", "minCoverage", "adapters"]


def test_set_channels_secondary_channels_nolink(single_con):

    single_con._set_channels()

    assert single_con.secondary_channels["SIDE_phred"][1]["end"] == []


def test_set_channels_secondary_chanels_link(multi_forks):

    multi_forks._set_channels()

    assert [multi_forks.secondary_channels["SIDE_phred"][1]["end"],
            multi_forks.secondary_channels["SIDE_max_len"][1]["end"],
            multi_forks.secondary_channels["SIDE_max_len"][3]["end"]] == \
           [[], ["SIDE_max_len_5"], ["SIDE_max_len_7"]]


def test_set_secondary_inputs_single(single_con):

    single_con._set_channels()
    single_con._set_secondary_inputs()

    p = single_con.processes[0]

    assert [p._context["forks"], p._context["secondary_inputs"]] == \
           ["\nIN_fastq_raw.set{ integrity_coverage_in_1_0 }\n",
            "IN_genome_size = Channel.value(params.genomeSize)\n"
            "IN_min_coverage = Channel.value(params.minCoverage)\n"
            "IN_adapters = Channel.value(params.adapters)"]


def test_set_secondary_inputs_raw_forks(raw_forks):

    raw_forks._set_channels()
    raw_forks._set_secondary_inputs()

    p = raw_forks.processes[0]

    assert [p._context["forks"], p._context["secondary_inputs"]] == \
           ["\nIN_fastq_raw.into{ integrity_coverage_in_0_0;"
            "patho_typing_in_0_2;seq_typing_in_0_3 }\n",
            "IN_genome_size = Channel.value(params.genomeSize)\n"
            "IN_min_coverage = Channel.value(params.minCoverage)\n"
            "IN_adapters = Channel.value(params.adapters)\n"
            "IN_pathoSpecies = Channel.value(params.pathoSpecies)"]


def test_set_secondary_inputs_multi_raw(single_con_multi_raw):

    single_con_multi_raw._set_channels()
    single_con_multi_raw._set_secondary_inputs()

    p = single_con_multi_raw.processes[0]

    assert [p._context["main_inputs"], p._context["secondary_inputs"]] == \
           ["IN_fasta_raw = Channel.fromPath(params.fasta).map{ it -> ["
            "it.toString().tokenize('/').last().tokenize('.').first(), it] }"
            "\nIN_fastq_raw = Channel.fromFilePairs(params.fastq)",
            "IN_assembly_mapping_opts = Channel.value(["
            "params.minAssemblyCoverage,params.AMaxContigs])\nIN_genome_size"
            " = Channel.value(params.genomeSize)"]


def test_set_secondary_channels(multi_forks):

    multi_forks._set_channels()
    multi_forks._set_secondary_channels()

    p = multi_forks.processes[1]

    print(multi_forks.main_raw_inputs)

    print(p._context)

    assert [p._context["output_channel"], p._context["forks"]] == \
        ["_integrity_coverage_out_1_0",
         "\n_integrity_coverage_out_1_0.into{ integrity_coverage_out_1_0;"
         "spades_in_1_4;skesa_in_1_5 }\n\n\nSIDE_max_len_1.set{"
         " SIDE_max_len_5 }\n"]


def test_set_secondary_channels_2(multi_forks):

    multi_forks._set_channels()
    multi_forks._set_secondary_channels()

    p = multi_forks.processes[4]

    assert [p._context["output_channel"], p.main_forks] == \
           ["_check_coverage_out_3_3",
            ["check_coverage_out_3_3", "spades_in_3_6", "skesa_in_3_7"]]


def test_set_implicit_link(implicit_link):

    implicit_link._set_channels()
    implicit_link._set_secondary_channels()

    p = implicit_link.processes[2]

    assert p.main_forks == ["fastqc_out_1_1", "_LAST_fastq_4"]


def test_set_implicit_link(implicit_link_2):

    implicit_link_2._set_channels()
    implicit_link_2._set_secondary_channels()

    p = implicit_link_2.processes[1]

    assert p.main_forks == ["integrity_coverage_out_1_0", "_LAST_fastq_3"]


def test_set_status_channels_multi(single_con):

    single_con._set_channels()
    single_con._set_status_channels()

    p = [x for x in single_con.processes[::-1]
         if isinstance(x, pc.StatusCompiler)][0]

    assert p._context["status_channels"] == \
               "STATUS_integrity_coverage_1.mix(STATUS_fastqc2_2," \
               "STATUS_fastqc2_report_2)"


def test_set_status_channels_single(single_status):

    single_status._set_channels()
    single_status._set_status_channels()

    p = [x for x in single_status.processes[::-1]
         if isinstance(x, pc.StatusCompiler)][0]

    assert p._context["status_channels"] == "STATUS_spades_1"


def test_set_compiler_channels(single_status):

    single_status._set_channels()
    single_status._set_compiler_channels()

    p = [x for x in single_status.processes[::-1]
         if isinstance(x, pc.StatusCompiler)][0]

    assert p._context["status_channels"] == "STATUS_spades_1"


def test_set_status_channels_no_status(single_status):

    single_status.processes[1].status_channels = []

    single_status._set_channels()
    single_status._set_status_channels()

    with pytest.raises(IndexError):
        p = [x for x in single_status.processes[::-1]
             if isinstance(x, pc.StatusCompiler)][0]


def test_set_status_channels_duplicate_status(single_status):

    single_status.processes[1].status_channels = ["A", "A"]

    single_status._set_channels()

    with pytest.raises(eh.ProcessError):
        single_status._set_status_channels()


def test_build(multi_forks):

    multi_forks.build()
    os.remove("teste.nf")

    assert multi_forks.template != ""

