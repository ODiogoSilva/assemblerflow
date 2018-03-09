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

    process myProcess {

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

- ``include "post.txt"`` (**Recommended**): Inserts
  ``beforeScript`` and ``afterScript`` statements to the process. These
  include a bash script that created a series of *dotfiles* for the process
  and scripts for sending requests to REST APIs (only when certain pipeline
  parameters are used). We recommend the inclusion of this placeholder to
  to ensure that the reports of a pipeline are correctly created for
  latter visualization (see :ref:`dotfiles` for more information).

- ``input_channel`` (**Mandatory**): All process must include an input channel.

- ``output_channel`` (**Optional**): Terminal processes may skip the output
  channel entirely. However, if you want to link the main output of this
  process with subsequent ones, this placeholder must be used.

- ``include "compiler_channels.txt"`` (**Recommended**): This will include the
  special channels that will compile the status/logging of the processes
  throughout the pipeline (see `Status channels`_).

- ``forks`` (**Conditional**): Inserts potential forks of the main output
  channel. It is **mandatory** if the ``output_channel`` is set.

- ``pid`` (**Optional**): This placeholder is used for secondary output
  channels, such as those that send run status information (see
  `Status channels`_).

As an example of a complete process, this is the template of ``spades.nf``::

    process spades {

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
between process. This class should be created in the
:mod:`assemblerflow.generator.process` module and inherit from the
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
                "channel": "IN_min_coverage = "
                           "Channel.value(params.minCoverage)"
            }
        ]

This process will receive two secondary inputs that are given by the
``genomeSize`` and ``minCoverage`` parameters. These should be made available
in the ``nextflow.config`` file. For each of these parameters, the dictionary
also stores how the channel should be defined at the beginning of the pipeline
file. Note that this channel definition mentions the parameters (e.g.
``params.genomeSize``).

.. note::
    In future versions, the parameters will be dynamically generated in the
    nextflow.config file

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