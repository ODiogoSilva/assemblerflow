import sys
import logging

from collections import defaultdict

logger = logging.getLogger("main.{}".format(__name__))

try:
    import generator.process as pc
    import generator.error_handling as eh
    from generator import header_skeleton as hs
except ImportError as e:
    import assemblerflow.generator.process as pc
    import assemblerflow.generator.error_handling as eh
    from assemblerflow.generator import header_skeleton as hs


process_map = {
        "integrity_coverage": pc.IntegrityCoverage,
        "seq_typing": pc.SeqTyping,
        "patho_typing": pc.PathoTyping,
        "check_coverage": pc.CheckCoverage,
        "fastqc": pc.FastQC,
        "trimmomatic": pc.Trimmomatic,
        "fastqc_trimmomatic": pc.FastqcTrimmomatic,
        "skesa": pc.Skesa,
        "spades": pc.Spades,
        "process_spades": pc.ProcessSpades,
        "assembly_mapping": pc.AssemblyMapping,
        "pilon": pc.Pilon,
        "mlst": pc.Mlst,
        "abricate": pc.Abricate,
        "prokka": pc.Prokka,
        "chewbbaca": pc.Chewbbaca,
        "status_compiler": pc.StatusCompiler,
        "trace_compiler": pc.TraceCompiler
}
"""
dict: Maps the process ids to the corresponding template interface class
"""


class NextflowGenerator:

    def __init__(self, process_list, nextflow_file):

        # Check if all specified processes are available
        for p in process_list:
            pname = p["input"]["process"]
            if pname not in process_map and pname != "__init__":
                logger.error("The process '{}' is not available".format(pname))
                sys.exit(1)

        self.processes = []

        self.processes = [pc.Init(template="init")]
        """
        list: Stores the process interfaces in the specified order
        """

        self._fork_tree = defaultdict(list)

        self._build_connections(process_list)

        self.nf_file = nextflow_file
        """
        str: Path to file where the pipeline will be generated
        """

        self.template = ""
        """
        str: String that will harbour the pipeline code
        """

        self.secondary_channels = {}
        """
        dict: Stores secondary channel links
        """

        self.main_raw_inputs = {}
        """
        list: Stores the main raw inputs from the user parameters into the
        first process(es).
        """

        self.secondary_inputs = {}
        """
        dict: Stores the secondary input channels that may be required by
        some processes. The key is the params variable and the key is the
        channel definition for nextflow::

            {"genomeSize": "IN_genome_size = Channel.value(params.genomeSize)"}

        """

        self.status_channels = []
        """
        list: Stores the status channels from each process
        """

        # self._check_pipeline_requirements()

    def _build_connections(self, process_list):
        """

        Returns
        -------

        """

        logger.debug("=============================")
        logger.debug("Building pipeline connections")
        logger.debug("=============================")

        for p, con in enumerate(process_list):

            logger.debug("Processing connection '{}': {}".format(p, con))

            # Get lanes
            in_lane = con["input"]["lane"]
            out_lane = con["output"]["lane"]
            logger.debug("[{}] Input lane: {}".format(p, in_lane))
            logger.debug("[{}] Output lane: {}".format(p, out_lane))

            p_in_name = con["input"]["process"]
            logger.debug("[{}] Input channel: {}".format(p, p_in_name))
            p_out_name = con["output"]["process"]
            logger.debug("[{}] Output channel: {}".format(p, p_out_name))

            # Instance output process
            out_process = process_map[p_out_name](template=p_out_name)
            input_suf = "{}_{}".format(in_lane, p)
            output_suf = "{}_{}".format(out_lane, p)
            logger.debug("[{}] Setting main channels with input suffix '{}'"
                         " and output suffix '{}'".format(p, input_suf,
                                                          output_suf))
            out_process.set_main_channel_names(input_suf, output_suf, out_lane)

            # Instance input process, if it exists. In case of init, the
            # output process forks from the raw input user data
            if p_in_name != "__init__":
                in_process = process_map[p_in_name](template=p_in_name)
                # Test if two processes can be connected by input/output types
                logger.debug("[{}] Testing connection between input and "
                             "output processes".format(p))
                self._test_connection(in_process, out_process)
                out_process.parent_lane = in_lane
            else:
                out_process.parent_lane = None

            # If the current connection is a fork, add it to the fork tree
            if in_lane != out_lane:
                logger.debug("[{}] Connection is a fork. Adding lanes to "
                             "fork list".format(p))
                self._fork_tree[in_lane].append(out_lane)
                # Update main output fork of parent process
                try:
                    parent_fork = [x for x in self.processes
                                   if x.lane == in_lane and
                                   x.template == p_in_name][0]
                    logger.debug("[{}] Updating main forks of parent fork "
                                 "'{}' with '{}'".format(
                                    p, parent_fork, out_process.input_channel))
                    parent_fork.update_main_forks(out_process.input_channel)
                except IndexError:
                    pass
            else:
                parent_process = self.processes[-1]
                if parent_process.output_channel:
                    logger.debug(
                        "[{}] Updating input channel of output process"
                        " with '{}'".format(
                            p, parent_process.output_channel))
                    out_process.input_channel = parent_process.output_channel

            self.processes.append(out_process)

    @staticmethod
    def _test_connection(parent_process, child_process):
        """Tests if two processes can be connected by input/output type

        Parameters
        ----------
        parent_process : assemblerflow.Process.Process
            Process that will be sending output.
        child_process : assemblerflow.Process.Process
            Process that will receive output.

        """

        # If any of the processes has an ignore type attribute set to True,
        # don't perform the check
        if parent_process.ignore_type or child_process.ignore_type:
            return

        if parent_process.output_type != child_process.input_type:
            logger.error(
                "The output of the '{}' process ({}) cannot link with the "
                "input of the '{}' process ({}). Please check the order of "
                "the processes".format(parent_process.template,
                                       parent_process.output_type,
                                       child_process.template,
                                       child_process.input_type))
            sys.exit(1)

    def _check_pipeline_requirements(self):
        """ Checks for some pipeline requirements before building

        Currently, the only hard requirement is that the pipeline must start
        with the integrity_coverage process, in order to evaluate if the
        input FastQ are corrupt or not.

        Besides this requirements, it checks for the existence the dependencies
        for all processes.
        """

        pipeline_names = [x.template for x in self.processes]

        logger.debug("Checking pipeline requirements for template "
                     "list: {}".format(pipeline_names))

        # Check if the pipeline contains at least one process with raw input
        # type
        raw_processes = [p for p in self.processes if p.input_type == "raw"]
        if not raw_processes:
            raise eh.ProcessError("At least one process with 'raw' input type "
                                 "must be specified. Check if the "
                                 "pipeline starts with an appropriate starting"
                                 " process.")

        logger.debug("Checking for dependencies of templates")

        for p in [i for i in self.processes if i.dependencies]:
            if not set(p.dependencies).issubset(set(pipeline_names)):
                raise eh.ProcessError(
                    "Missing dependencies for process {}: {}".format(
                        p.template, p.dependencies))

    def _build_header(self):
        """Adds the header template to the master template string
        """

        logger.debug("===============")
        logger.debug("Building header")
        logger.debug("===============")
        self.template += hs.header

    def _update_raw_input(self, p):
        """Given a process, this method updates the
        :attr:`~Process.main_raw_inputs` attribute with the corresponding
        raw input channel of that process

        Parameters
        ----------
        p : assemblerflow.Process.Process
        """

        logger.debug("[{}] Setting raw input channel".format(p.template))
        raw_in = p.get_user_channel()

        if p.input_type in self.main_raw_inputs:
            self.main_raw_inputs[p.input_type]["raw_forks"].append(
                raw_in["input_channel"])
        else:
            self.main_raw_inputs[p.input_type] = {
                "channel": raw_in["channel"],
                "channel_str": raw_in["channel_str"],
                "raw_forks": [raw_in["input_channel"]]
            }

    def _update_secondary_inputs(self, p):
        """Given a process, this method updates the
        :attr:`~Process.secondary_inputs` attribute with the corresponding
        secondary inputs of that channel.

        Parameters
        ----------
        p : assemblerflow.Process.Process
        """

        logger.debug("[{}] Checking secondary links".format(p.template))
        if p.secondary_inputs:
            logger.debug("[{}] Found secondary input channel(s): "
                         "{}".format(p.template, p.secondary_inputs))
            for ch in p.secondary_inputs:
                if ch["params"] not in self.secondary_inputs:
                    logger.debug("[{}] Added channel: {}".format(
                        p.template, ch["channel"]))
                    self.secondary_inputs[ch["params"]] = ch["channel"]

    def _get_fork_tree(self, p):
        """

        Parameters
        ----------
        p

        Returns
        -------
        """

        lane = p.lane
        parent_lanes = [lane]

        while True:
            original_lane = lane
            for fork_in, fork_out in self._fork_tree.items():
                if lane in fork_out:
                    lane = fork_in
                    parent_lanes.append(fork_in)
            if lane == original_lane:
                break

        return parent_lanes

    def _update_secondary_channels(self, p):
        """

        Parameters
        ----------
        p : assemblerflow.Process.Process

        """

        # Check if the current process has a start of a secondary
        # side channel
        if p.link_start:
            logger.debug("[{}] Found secondary link start: {}".format(
                p.template, p.link_start))
            for l in p.link_start:
                self.secondary_channels[l] = {p.lane: {"p": p, "end": []}}

        # check if the current process receives a secondary side channel.
        # If so, add to the links list of that side channel
        if p.link_end:
            logger.debug("[{}] Found secondary link end: {}".format(
                p.template, p.link_end))
            for l in p.link_end:

                parent_forks = self._get_fork_tree(p)

                # Parse special case where the secondary channel links with
                # the main output of the specified type
                if l["link"].startswith("__"):
                    output_type = l["link"].lstrip("_")
                    for proc in self.processes[::-1]:
                        if proc.lane not in parent_forks:
                            continue
                        if proc.output_type == output_type:
                            proc.update_main_forks("{}_{}".format(
                                l["alias"], p.pid))
                            logger.debug(
                                "[{}] Found special implicit link '{}' with "
                                "output type '{}'. Linked '{}' with process "
                                "{}".format(
                                    p.template, l["link"], output_type,
                                    l["alias"], proc))
                            break
                    continue

                if l["link"] not in self.secondary_channels:
                    continue

                for lane in parent_forks:
                    if lane in self.secondary_channels[l["link"]]:
                        self.secondary_channels[
                            l["link"]][lane]["end"].append("{}".format(
                                "{}_{}".format(l["alias"], p.pid)))

        logger.debug("[{}] Secondary links updated: {}".format(
            p.template, self.secondary_channels))

    def _set_channels(self):
        """Sets the main channels for the pipeline

        The setup of the main channels follows four main steps for each
        process specified in the :py:attr:`NextflowGenerator.processes`
        attribute:

            - (If not the first process) Checks if the input of the current
            process is compatible with the output of the previous process.
            - Checks if the current process has starts any secondary channels.
            If so, populate the :py:attr:`NextflowGenerator.secondary_channels`
            with the name of the link start, the process class and a list
            to harbour potential receiving ends.
            - Checks if the current process receives from any secondary
            channels. If a corresponding secondary link has been previously
            set, it will populate the
            :py:attr:`NextflowGenerator.secondary_channels` attribute with
            the receiving channels.
            - Sets the main channels by providing the process ID.

        Notes
        -----
        **On the secondary channel setup**: With this approach, there can only
        be one secondary link start for each type of secondary link. For
        instance, If there are two processes that start a secondary channel
        for the ``SIDE_max_len`` channel, only the last one will be recorded,
        and all receiving processes will get the channel from the latest
        process.
        """

        logger.debug("=====================")
        logger.debug("Setting main channels")
        logger.debug("=====================")

        for i, p in enumerate(self.processes):

            # Set main channels for the process
            logger.debug("[{}] Setting main channels with pid: {}".format(
                p.template, i))
            p.set_channels(pid=i)

            # If there is no parent lane, set the raw input channel from user
            if not p.parent_lane and p.input_type:
                self._update_raw_input(p)

            self._update_secondary_inputs(p)

            self._update_secondary_channels(p)

    def _set_secondary_inputs(self):

        logger.debug("========================")
        logger.debug("Setting secondary inputs")
        logger.debug("========================")

        # Get init process
        init_process = self.processes[0]
        logger.debug("Setting main raw inputs: "
                     "{}".format(self.main_raw_inputs))
        init_process.set_raw_inputs(self.main_raw_inputs)
        logger.debug("Setting secondary inputs: "
                     "{}".format(self.secondary_inputs))
        init_process.set_secondary_inputs(self.secondary_inputs)

    def _set_secondary_channels(self):
        """Sets the secondary channels for the pipeline

        This will iterate over the
        :py:attr:`NextflowGenerator.secondary_channels` dictionary that is
        populated when executing :py:func:`NextflowGenerator._set_channels`
        method.
        """

        logger.debug("==========================")
        logger.debug("Setting secondary channels")
        logger.debug("==========================")

        logger.debug("Setting secondary channels: {}".format(
            self.secondary_channels))

        for source, lanes in self.secondary_channels.items():

            for lane, vals in lanes.items():

                if not vals["end"]:
                    logger.debug("[{}] No secondary links to setup".format(
                        vals["p"].template))
                    continue

                logger.debug("[{}] Setting secondary links for "
                             "source {}: {}".format(vals["p"].template,
                                                    source,
                                                    vals["end"]))

                vals["p"].set_secondary_channel(source, vals["end"])

    def _set_status_channels(self):
        """Compiles all status channels for the status compiler process
        """

        # Compile status channels from pipeline process
        status_channels = []
        for p in [p for p in self.processes if p.ptype != "status"]:
            status_channels.extend(p.status_strs)

        logger.debug("Setting status channels: {}".format(status_channels))

        # Check for duplicate channels. Raise exception if found.
        if len(status_channels) != len(set(status_channels)):
            raise eh.ProcessError(
                "Duplicate status channels detected. Please ensure that "
                "the 'status_channels' attributes of each process are "
                "unique. Here are the status channels:\n\n{}".format(
                    ", ".join(status_channels)
                ))

        for p in self.processes:
            if p.ptype == "status":
                p.set_status_channels(status_channels)

    def build(self):
        """Main pipeline builder

        This method is responsible for building the
        :py:attr:`NextflowGenerator.template` attribute that will contain
        the nextflow code of the pipeline.

        First it builds the header, then sets the main channels, the
        secondary channels and finally the status channels. When the pipeline
        is built, is writes the code to a nextflow file.
        """

        # Generate regular nextflow header that sets up the shebang, imports
        # and all possible initial channels
        self._build_header()

        self._set_channels()

        self._set_secondary_inputs()

        self._set_secondary_channels()

        # self._set_status_channels()

        for p in self.processes:
            self.template += p.template_str

        with open(self.nf_file, "w") as fh:
            fh.write(self.template)