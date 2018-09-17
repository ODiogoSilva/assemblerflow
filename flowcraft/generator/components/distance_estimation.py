
try:
    from generator.process import Process
except ImportError:
    from flowcraft.generator.process import Process


class PatlasMashDist(Process):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.input_type = "fasta"
        self.output_type = "json"

        self.params = {
            "pValue": {
                "default": 0.05,
                "description": "P-value cutoff for the distance estimation "
                               "between two sequences to be included in the "
                               "output."
            },
            "mash_distance": {
                "default": 0.1,
                "description": "Sets the maximum distance between two "
                               "sequences to be included in the output."
            },
            "shared_hashes": {
                "default": 0.8,
                "description": "Sets a minimum percentage of hashes shared "
                               "between two sequences in order to include its "
                               "result in the output."
            },
            "refFile": {
                "default": "'/ngstools/data/plasmid_db_reference.msh'",
                "description": "Specifies the reference file to be provided "
                               "to mash. It can either be a fasta or a .msh "
                               "reference sketch generated by mash."
            }
        }

        self.directives = {
            "runMashDist": {
                "container": "flowcraft/mash-patlas",
                "version": "1.5.2-1",
                "cpus": 1,
                "memory": "{ 4.GB * task.attempt }"
            },
            "mashDistOutputJson": {
                "container": "flowcraft/mash-patlas",
                "version": "1.5.2-1",
                "cpus": 1,
                "memory": "'4GB'"
            }
        }

        self.status_channels = [
            "runMashDist",
            "mashDistOutputJson"
        ]

        self.link_end.append({
            "link": "SIDE_mashSketchOutChannel",
            "alias": "SIDE_mashSketchOutChannel"
        })


class PatlasMashScreen(Process):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.input_type = "fastq"
        self.output_type = "json"

        self.params = {
            "noWinner": {
                "default": "false",
                "description": "A variable that enables the use of -w option"
                               " for mash screen."
            },
            "pValue": {
                "default": 0.05,
                "description": "P-value cutoff for the distance estimation "
                               "between two sequences to be included in the "
                               "output."
            },
            "identity": {
                "default": 0.9,
                "description": "The percentage of identity between the reads "
                               "input and the reference sequence"
            },
            "refFile": {
                "default": "'/ngstools/data/plasmid_db_reference.msh'",
                "description": "Specifies the reference file to be provided "
                               "to mash. It can either be a fasta or a .msh "
                               "reference sketch generated by mash."
            }
        }

        self.directives = {
            "mashScreen": {
                "container": "flowcraft/mash-patlas",
                "version": "1.5.2-1",
                "cpus": 1,
                "memory": "{ 4.GB * task.attempt }"
            },
            "mashOutputJson": {
                "container": "flowcraft/mash-patlas",
                "version": "1.5.2-1",
                "cpus": 1,
                "memory": "'4GB'"
            }
        }

        self.status_channels = [
            "mashScreen",
            "mashOutputJson"
        ]

        self.compiler["patlas_consensus"] = ["mashScreenOutputChannel"]

        self.link_end.append({
            "link": "SIDE_mashSketchOutChannel",
            "alias": "SIDE_mashSketchOutChannel"
        })


class MashSketchFasta(Process):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.input_type = "fasta"
        self.output_type = "msh"

        self.ignore_type = True

        self.params = {
            "kmerSize": {
                "default": 21,
                "description": "Set the kmer size for hashing. Default: 21."
            },
            "sketchSize": {
                "default": 1000,
                "description": "Set the number of hashes per sketch. Default: "
                               "1000"
            },
        }

        self.directives = {
            "mashSketchFasta": {
                "container": "flowcraft/mash-patlas",
                "version": "1.4.1",
                "cpus": 1,
                "memory": "{ 4.GB * task.attempt }"
            },
        }

        self.status_channels = [
            "mashSketchFasta",
        ]

        self.link_start.extend(["SIDE_mashSketchOutChannel"])


class MashSketchFastq(MashSketchFasta):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.input_type = "fastq"

        # add more params to dict
        self.params.update({
            "minKmer": {
                "default": 1,
                "description": "Minimum copies of each k-mer required to pass "
                               "noise filter for reads. Implies -r. Default: 1"
            },
            "genomeSize": {
                "default": "false",
                "description": "Genome size (raw bases or with K/M/G/T). If "
                               "specified, will be used for p-value calculation"
                               " instead of an estimated size from k-mer "
                               "content. Default: false, meaning that it won't"
                               "be used. If you want to use it pass a number to"
                               " this parameter."
            }
        })

        self.directives = {
            "mashSketchFastq": self.directives["mashSketchFasta"]
        }

        self.status_channels = [
            "mashSketchFastq",
        ]


class FastAniMatrix(Process):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.input_type = "fasta"
        self.output_type = "out"

        # add more params to dict
        self.params.update({
            "minKmer": {
                "default": 1,
                "description": "Minimum copies of each k-mer required to pass "
                               "noise filter for reads. Implies -r. Default: 1"
            },
            "genomeSize": {
                "default": "false",
                "description": "Genome size (raw bases or with K/M/G/T). If "
                               "specified, will be used for p-value calculation"
                               " instead of an estimated size from k-mer "
                               "content. Default: false, meaning that it won't"
                               "be used. If you want to use it pass a number to"
                               " this parameter."
            }
        })

        self.directives = {
            "fastAniMatrix": {
                "container": "flowcraft/fast_ani",
                "version": "1.1.0",
                "cpus": 1,
                "memory": "{ 4.GB * task.attempt }"
            },
        }

        self.status_channels = [
            "fastAniMatrix",
        ]
