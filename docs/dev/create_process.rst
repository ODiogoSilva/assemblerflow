Process creation guidelines
===========================

Basic process creation
----------------------

The addition of a new process to assemblerflow requires three main steps:

#. `Create process template`_: Create a jinja2 template in ``assemblerflow.generator.templates`` with the
   nextflow code.

#. `Create Process class`_: Create a :class:`~assemblerflow.generator.process.Process` subclass in
   :class:`assemblerflow.generator.process` with
   information about the process (e.g., expected input/output, secondary inputs,
   etc.).

#. `Add to available processes`_: Add the :class:`~assemblerflow.generator.process` class to the
   dictionary of available process in
   :attr:`assemblerflow.generator.engine.process_map`.

.. _create-process:

Create process template
:::::::::::::::::::::::

First, create the nextflow template that will be integrated into the pipeline
as a process. This file must be placed in ``assemblerflow.generator.templates``
and have the ``.nf`` extension. In order to allow the template to be
dynamically added to a pipeline file, we use the jinja2_ template language to
substitute key variables in the process, such as input/output channels.

A minimal example created as a ``my_process.nf`` file is as follows::

    process myProcess_{{ pid }} {

    {% include "post.txt" ignore missing %}

    input:
    <input variables> from {{ input_channel }}

    // The output is optional
    output:
    <output variables> into {{ output_channel }}
    {% with task_name="abricate" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    """
    <process code/commands>
    """

    }

    {{ forks }}

The fields surrounded by curly brackets are jinja placeholders that will be
dynamically interpolated when building the pipeline, ensuring that the
processes and potential forks correctly link with each other. This example
contains all placeholder variables that are currently supported by
assemblerflow:


- ``pid`` (**Mandatory**): This placeholder is used as a unique process
  identifier that prevent issues from process duplication in the pipeline.
  It is also important for for unique secondary output channels, such as
  those that send run status information (see `Status channels`_).

- ``include "post.txt"`` (**Mandatory**): Inserts
  ``beforeScript`` and ``afterScript`` statements to the process that setup
  environmental variables and a series of *dotfiles* for the process to
  log their status, warnings, fails and reports (see :ref:`dotfiles` for
  more information). It also includes scripts for sending requests to
  REST APIs (only when certain pipeline parameters are used).

- ``input_channel`` (**Mandatory**): All process must include **one and only
  one** input channel.

- ``output_channel`` (**Optional**): Terminal processes may skip the output
  channel entirely. However, if you want to link the main output of this
  process with subsequent ones, this placeholder must be used **only once**.

- ``include "compiler_channels.txt"`` (**Mandatory**): This will include the
  special channels that will compile the status/logging of the processes
  throughout the pipeline. **You must include the
  whole block** (see `Status channels`_)::

    {% with task_name="abricate" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}


- ``forks`` (**Conditional**): Inserts potential forks of the main output
  channel. It is **mandatory** if the ``output_channel`` is set.

As an example of a complete process, this is the template of ``spades.nf``::

    process spades_{{ pid }} {

        // Send POST request to platform
        {% include "post.txt" ignore missing %}

        tag { fastq_id + " getStats" }
        publishDir 'results/assembly/spades/', pattern: '*_spades.assembly.fasta', mode: 'copy'

        input:
        set fastq_id, file(fastq_pair), max_len from {{ input_channel }}.join(SIDE_max_len_{{ pid }})
        val opts from IN_spades_opts
        val kmers from IN_spades_kmers

        output:
        set fastq_id, file('*_spades.assembly.fasta') optional true into {{ output_channel }}
        set fastq_id, val("spades"), file(".status"), file(".warning"), file(".fail") into STATUS_{{ pid }}
        file ".report.json"

        when:
        params.stopAt != "spades"

        script:
        template "spades.py"

    }

    {{ forks }}


Create Process class
::::::::::::::::::::

The process class will contain the information that assemblerflow
will use to build the pipeline and assess potential conflicts/dependencies
between process. This class should be created in one the category files in the
:mod:`assemblerflow.generator.components` module (e.g.: ``assembly.py``). If
the new component does not fit in any of the existing categories, create a
new one that imports :mod:`assemblerflow.generator.process.Process` and add
your new class. This class should inherit from the
:class:`~assemblerflow.generator.process.Process` base
class::

    class MyProcess(Process):

        def __init__(self, **kwargs):

            super().__init__(**kwargs)

            self.input_type = "fastq"
            self.output_type = "fasta"

This is the simplest working example of a process class, which basically needs
to inherit the parent class attributes (the ``super`` part).
Then we only need to define the expected input
and output types of the process. There are no limitations to the
input/output types.
However, a pipeline will only build successfully when all processes correctly
link the output with the input type.

Depending on the process, other attributes may be required:

    - `Parameters`_: Parameters provided by the user to be used in the process.
    - `Secondary inputs`_: Channels created from parameters provided by the
      user.
    - Secondary `Link start`_ and `Link end`_: Secondary links that connect
      secondary information between two processes.
    - `Dependencies`_: List of other processes that may be required for
      the current process.
    - `Directives`_: Default information for RAM/CPU/Container directives
      and more.

Add to available processes
::::::::::::::::::::::::::

The final step is to add your new process to the list of available processes.
This list is defined in :attr:`assemblerflow.generator.engine.process_map`
module, which is a dictionary
mapping the process template name to the corresponding template class::

    process_map = {
    <other_process>
    "my_process_template": process.MyProcess
    }

Note that the template string does not include the ``.nf`` extension.

Process attributes
------------------

This section describes the main attributes of the
:mod:`~assemblerflow.generator.process.Process` class: what they
do and how do they impact the pipeline generation.

Input/Output types
::::::::::::::::::

The :attr:`~assemblerflow.generator.process.Process.input_type` and
:attr:`~assemblerflow.generator.process.Process.output_type` attributes
set the expected type of input and output of the process. There are no
limitations to the type of input/output that are provided. However, processes
will only link when the output of one process matches the input of the
subsequent process (unless the
:attr:`~assemblerflow.generator.process.Process.ignore_type` attribute is set
to ``True``). Otherwise, assemblerflow will raise an exception stating that
two processes could not be linked.

.. note::

    The input/ouput types that are currently used are ``fastq``, ``fasta``.

Parameters
::::::::::

The :attr:`~assemblerflow.generator.process.Process.params` attribute sets
the parameters that can be used by the process. For each parameter, a default
value and a description should be provided. The default value will be set
in the ``params.config`` file in the pipeline directory and the description
will be used to generated the custom help message of the pipeline::

    self.params = {
        "genomeSize": {
            "default": 2.1,
            "description": "Expected genome size (default: params.genomeSiz)
        },
        "minCoverage": {
            "default": 15,
            "description": "Minimum coverage to proceed (default: params.minCoverage)"
        }
    }

These parameters can be simple values that are not feed into
any channel, or can be automatically set to a secondary input channel via
`Secondary inputs`_ (see below).

They can be specified when running the pipeline like any nextflow parameter
(e.g.: ``--genomeSize 5``) and used in the nextflow process as usual
(e.g.: ``params.genomeSize``).

.. note::
    These pairs are then used to populate the ``params.config`` file that is
    generated in the pipeline directory. Note that the values are replaced
    literally in the config file. For instance, ``"genomeSize": 2.1,`` will appear
    as ``genomeSize = 2.1``, whereas ``"adapters": "'None'"`` will appear as
    ``adapters = 'None'``. If you want a value to appear as a string, the double
    and single quotes are necessary.


Secondary inputs
::::::::::::::::

Any process can receive one or more input channels in addition to the main
channel. These are particularly useful when the process needs to receive
additional options from the ``parameters`` scope of nextflow.
These additional inputs can be specified via the
:attr:`~assemblerflow.generator.process.Process.secondary_inputs` attribute,
which should store a list of dictionaries (a dictionary for each input). Each dictionary should
contains a key:value pair with the name of the parameter (``params``) and the
definition of the nextflow channel (``channel``). Consider the example below::

    self.secondary_inputs = [
            {
                "params": "genomeSize",
                "channel": "IN_genome_size = Channel.value(params.genomeSize)"
            },
            {
                "params": "minCoverage",
                "channel": "IN_min_coverage = Channel.value(params.minCoverage)"
            }
        ]

This process will receive two secondary inputs that are given by the
``genomeSize`` and ``minCoverage`` parameters. These should be also specified
in the :attr:`~assemblerflow.generator.process.Process.params` attribute
(See `Parameters`_ above).

For each of these parameters, the dictionary
also stores how the channel should be defined at the beginning of the pipeline
file. Note that this channel definition mentions the parameters (e.g.
``params.genomeSize``). An additional best practice for channel definition
is to include one or more sanity checks to ensure that the provided arguments
are correct. These checks can be added in the nextflow template file, or
literally in the ``channel`` string::

    self.secondary_inputs = [
        {
            "params": "genomeSize",
            "channel":
                    "IN_genome_size = Channel.value(params.genomeSize)"
                    "map{it -> it.toString().isNumber() ? it : exit(1, \"The genomeSize parameter must be a number or a float. Provided value: '${params.genomeSize}'\")}"
            }

Extra input
:::::::::::

The :attr:`~assemblerflow.generator.process.Process.extra_input` attribute
is mostly a user specified directive that allows the injection of additional
input data from a parameter into the main input channel of the process.
When a pipeline is defined as::

    process1 process2={'extra_input':'var'}

assemblerflow will expose a new ``var`` parameter, setup an extra input
channel and mix it with ``process2`` main input channel. A more detailed
explanation follows below.

First, assemblerflow will create a nextflow channel from the parameter name
provided via the ``extra_input`` directive. The channel string will depend
on the input type of the process (this string is fetched from the
:attr:`~assemblerflow.generator.process.Process.RAW_MAPPING` attribute).
For instance, if the input type of
``process2`` is ``fastq``, the new extra channel will be::

    IN_var_extraInput = Channel.fromFilePairs(params.var)

Since the same extra input parameter may be used by more than one process,
the ``IN_var_extraInput`` channel will be automatically forked into the
final destination channels::

    // When there is a single destination channel
    IN_var_extraInput.set{ EXTRA_process2_1_2 }
    // When there are multiple destination channels for the same parameter
    IN_var_extraInput.into{ EXTRA_process2_1_2; EXTRA_process3_1_3 }

The destination channels are the ones that will be actually mixed with
the main input channels::

    process process2 {
        input:
        (...) main_channel.mix(EXTRA_process2_1_2)
    }

In these cases, the processes that receive the extra input will process the
data provided by the preceding channel **AND** by the parameter. The data
provided via the extra input parameter does not have to wait for the
``main_channel``, which means that they can run in parallel, if there are
enough resources.

Link start
::::::::::

The :attr:`~assemblerflow.generator.process.Process.link_start` attribute
stores a list of strings of channel names that can be used as secondary
channels in the pipeline (See the `Secondary links between process`_ section).
By default, this attribute contains the main output channel, which means
that every process can fork the main channel to one or more receiving
processes.

Link end
::::::::

The :attr:`~assemblerflow.generator.process.Process.link_end` attribute
stores a list of dictionaries with channel names that are meant to be
received by the process as secondary channel **if** the corresponding
`Link start`_ exists in the pipeline. Each dictionary in this list will define
one secondary channel and requires two key:value pairs::

    self.link_end({
        "link": "SomeChannel",
        "alias": "OtherChannel")
    })

If another process exists in the pipeline with
``self.link_start.extend(["SomeChannel"])``, assemblerflow will automatically
establish a secondary channel between the two processes. If there are multiple
processes receiving from a single one, the channel from the later will
for into any number of receiving processes.

Dependencies
::::::::::::

If a process depends on the presence of one or more processes upstream in the
pipeline, these can be specific via the
:attr:`~assemblerflow.generator.process.Process.dependencies` attribute.
When building the pipeline if at least one of the dependencies is absent,
assemblerflow will raise an exception informing of a missing dependency.

Directives
::::::::::

The :attr:`~assemblerflow.generator.process.Process.directives` attribute
allows for information about cpu/RAM usage and container to be specified
for each nextflow process in the template file. For instance, considering
the case where a ``Process`` has a template with two nextflow processes::

    process proc_A_{{ pid }} {
        // stuff
    }

    process proc_B_{{ pid }} {
        // stuff
    }

Then, information about each process can be specified individually in the
:attr:`~assemblerflow.generator.process.Process.directives` attribute::


    class myProcess(Process):
        (...)
        self.directives = {
            "proc_A": {
                "cpus": 1
                "memory": "4GB"
            },
            "proc_B": {
                "cpus": 4
                "container": "my/container"
                "version": "1.0.0"
            }
        }

The information in this attribute will then be used to build the
``resources.config`` (containing the information about cpu/RAM) and
``containers.config`` (containing the container images) files. Whenever a
directive is missing, such as the ``container`` and ``version`` from ``proc_A``
and ``memory`` from ``proc_B``, nothing about them will be written into the
config files and they will use the default pipeline values. In the case
cpus, the default is ``1``, for RAM is ``1GB`` and if no container is
specified, the process will run locally.

Ignore type
:::::::::::

The :attr:`~assemblerflow.generator.process.Process.ignore_type` attribute,
controls whether a match between the input of the current process and the
output of the previous one is enforced or not. When there are multiple
terminal processes that fork from the main channel, there is no need to
enforce the type match and in that case this attribute can be set to ``False``.

Process ID
::::::::::

The process ID, set via the
:attr:`~assemblerflow.generator.process.Process.pid` attribute, is an
arbitrarily and incremental number that is awarded to each process depending
on its position in the pipeline. It is mainly used to ensure that there are
no duplicated channels even when the same process is used multiple times
in the same pipeline.

Template
::::::::

The :attr:`~assemblerflow.generator.process.Process.template` attribute
is used to fetch the jinja2 template file that corresponds to the current
process. The path to the template file is determined as follows::

    join(<template directory>, template + ".nf")


Status channels
:::::::::::::::

The status channels are special channels dedicated to passing information
regarding the status, warnings, fails and logging from each process
(see :ref:`dotfiles` for more information). They are used only when the
nextflow template file contains the appropriate jinja2 placeholder::

    output:
    {% with task_name="<nextflow_template_name>" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

By default,
every ``Process`` class contains a
:attr:`~assemblerflow.generator.process.Process.status_channels` list
attribute that contains the
:attr:`~assemblerflow.generator.process.Process.template` string::

    self.status_channels = ["STATUS_{}".format(template)]

If there is only one nextflow process in the template and the ``task_name``
variable in the template matches the
:attr:`~assemblerflow.generator.process.Process.template` attribute, then
it's all automatically set up.

If the template file contains **more than one nextflow process**
definition, multiple placeholders can be provided in the template::

    process A {
        (...)
        output:
        {% with task_name="A" %}
        {%- include "compiler_channels.txt" ignore missing -%}
        {% endwith %}
    }

    process B {
        (...)
        output:
        {% with task_name="B" %}
        {%- include "compiler_channels.txt" ignore missing -%}
        {% endwith %}
    }

In this case, the
:attr:`~assemblerflow.generator.process.Process.status_channels` attribute
would need to be changed to::

    self.status_channels = ["A", "B"]

Advanced use cases
------------------

Secondary links between process
:::::::::::::::::::::::::::::::

In some cases, it might be necessary to perform additional links between
two or more processes.
For example, the maximum read length might be gathered in one process, and
that information may be required by a subsequent process. These secondary
channels allow this information to be passed between theses channels.

These additional links are called secondary channels and
they may be explicitly or implicitly declared.

Explicit secondary channels
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create an explicit secondary channel, the origin or source of this channel
must be declared in the nextflow process that sends it::

    // secondary channels can be created inside the process
    output:
    <main output> into {{ output_channel }}
    <secondary output> into SIDE_max_read_len_{{ pid }}

    // or outside
    SIDE_phred_{{ pid }} = Channel.create()

Then, we add the information that this process has a secondary channel start
via the ``link_start`` list attribute in the corresponding
``assemblerflow.generator.process.Process`` class::

    class MyProcess(Process):

        (...)

        self.link_start.extend(["SIDE_max_read_len", "SIDE_phred"])

Notice that we extend the ``link_start`` list, instead of simply assigning.
This is because all processes already have the main channel as an implicit
link start (See `Implicit secondary channels`_).

**Now, any process that is executed after this one can receive this secondary
channel.**

For another process to receive this channel, it will be necessary to add this
information to the process class(es) via the ``link_end`` list attribute::

    class OtherProcess(Process):

        (...)

        self.link_end.append({
            "link": "SIDE_phred",
            "alias": "OtherName"
        })

Notice that now we append a dictionary with two key:values. The first, `link`
must match a string from the `link_start` list (in this case, `SIDE_phred`).
The second, `alias`, will be the channel name in the receiving process nextflow
template (which can be the same as the `link` value).

Now, we only need to add the secondary channel to the nextflow template, as in
the example below::

    input:
    <main_input> from {{ input_channel }}.mix(OtherName_{{ pid}})

Implicit secondary channels
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the main output of the channels is declared as a secondary channel
start. This means that any process can receive the main output channel as a
a secondary channel of a subsequent process. This can be useful in situations
were a post-assembly process (has ``assembly`` as expected input and output)
needs to receive the last channel with fastq files::

    class AssemblyMapping(Process):

        (...)

        self.link_end.append({
            "link": "MAIN_fq",
            "alias": "_MAIN_assembly"
        })

In this example, the ``AssemblyMapping`` process will receive a secondary
channel with from the last process that output fastq files into a channel
called ``_MAIN_assembly``. Then, this channel is received in the nextflow
template like this::

    input:
    <main input> from {{ input_channel }}.join(_{{ input_channel }})

Implicit secondary channels can also be used to
fork the last output channel into multiple terminal processes::

    class Abricate(Process):

        (...)

        self.link_end.append({
            "link": "MAIN_assembly",
            "alias": "MAIN_assembly"
        })

In this case, since ``MAIN_assembly`` is already the prefix of the main
output channel of this process, there is no need for changes in the process
template::

    input:
    <main input> from {{ input_channel }}


.. _jinja2: http://jinja.pocoo.org/docs/2.10/