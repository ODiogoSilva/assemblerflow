
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

        # self.dependencies = ["integrity_coverage"]

        self.params = {
            "phenix_config": {
                "default": "'templates/phenix.yaml'",
                "description":
                    "Path to a config file in YAML format for SNP calling with Phenix. "
                    "Default: $params.phenix_config"
            },
            "reference": {
                "default": "null",
                "description":
                    "Path to a reference genome. "
                    "Default: $params.reference"
            },
            "mapper": {
                "default": "'bwa'",
                "description":
                    "Mapper [bwa | bowtie2]. "
                    "Default: $params.mapper"
            },
            "variant": {
                "default": "'gatk'",
                "description":
                    "Mapper [gatk | mpileup]. "
                    "Default: $params.variant"
            },
            "extract_snps": {
                "default": "false",
                "description":
                    "Extract snps. "
                    "Default: $params.extract_snps"
            }
            # "gatk_jar": {
            #     "default": "'/home/ubuntu/data/miniconda2/opt/gatk-3.7/GenomeAnalysisTK.jar'",
            #     "description":
            #         "ENV PATH to GATK JAR file."
            #         "Default: $params.gatk_jar"
            # },
            # "picard_jar": {
            #     "default": "'/home/ubuntu/data/miniconda2/share/picard-2.11.0-0/picard.jar'",
            #     "description":
            #         "ENV PATH to PICARD JAR file."
            #         "Default: $params.picard_jar"
            # }
        }
        self.secondary_inputs = [
            {
                "params": "phenix_config",
                "channel": "IN_phenix_config = Channel.fromPath(params.phenix_config)"
            },
            {
                "params": "reference",
                "channel": "IN_reference_phenix = Channel.fromPath(params.reference)"
            }
        ]
        self.directives = {
        "phenix": {
            "cpus": 1,
            "memory": "{ 2.GB * task.attempt }",
            "container": "quay.io/thanhleviet/phenix",
            "version": "latest"
        },
        "extract_snps": {
            "cpus": 1,
            "memory": "{ 2.GB * task.attempt }",
            "container": "quay.io/biocontainers/snp-sites",
            "version": "2.4.0--ha92aebf_3"
        }
        }


class Snippy(Process):
    """Snippy process template interface
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.input_type = "fastq"
        self.output_type = "fasta"
    
        self.params = {
            "threads": {
                "default": "8",
                "description":
                    "Number of threads. "
                    "Default: $params.threads"
            },
            "reference": {
                "default": "null",
                "description":
                    "Path to a reference genome. "
                    "Default: $params.reference"
            },
            "core_genome": {
                "default": "false",
                "description":
                    "Extract core genome. "
                    "Default: $params.core_genome"
            }
        }
        self.secondary_inputs = [
            {
                "params": "reference",
                "channel": "IN_reference_snippy = Channel.fromPath(params.reference)"
            }
        ]
        self.directives = {
        "snippy": {
            "cpus": 1,
            "memory": "{ 2.GB * task.attempt }",
            "container": "quay.io/biocontainers/snippy",
            "version": "4.0_dev--1"
            },
        "snippy_core": {
            "cpus": 1,
            "memory": "{ 2.GB * task.attempt }",
            "container": "quay.io/biocontainers/snippy",
            "version": "4.0_dev--1"
            }
        }
