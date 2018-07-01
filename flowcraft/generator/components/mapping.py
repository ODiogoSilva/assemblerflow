
try:
    from generator.process import Process
except ImportError:
    from flowcraft.generator.process import Process


class Phenix(Process):
    """Phenix process template interface

    This process is set with:

        - ``input_type``: fastq
        - ``output_type``: assembly
        - ``ptype``: assembly

    It contains one **secondary channel link end**:

        - ``SIDE_max_len`` (alias: ``SIDE_max_len``): Receives max read length
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.input_type = "fastq"
        self.output_type = "fasta"

        # self.link_end.append({"link": "SIDE_max_len", "alias": "SIDE_max_len"})

        self.dependencies = ["integrity_coverage"]

        self.params = {
            "phenix_config": {
                "default": "null",
                "description":
                    "Path to a config file in YAML format for SNP calling with Phenix."
                    "Default: $params.phenix_config"
            },
            "reference": {
                "default": "null",
                "description":
                    "Path to a reference genome."
                    "Default: $params.reference"
            }
        }

        self.directives = {"phenix": {
            "cpus": 4,
            "memory": "{ 5.GB * task.attempt }",
            "container": "mbull/bioinformatics-containers",
            "version": "phenix"
            # "scratch": "true"
        }}


# class Snippy(Process):
#     """Skesa process template interface
#     """
#
#     def __init__(self, **kwargs):
#
#         super().__init__(**kwargs)
#
#         self.input_type = "fastq"
#         self.output_type = "fasta"
#
#         self.directives = {"skesa": {
#             "cpus": 4,
#             "memory": "{ 5.GB * task.attempt }",
#             "container": "flowcraft/skesa",
#             "version": "2.1-1",
#             "scratch": "true"
#         }}
