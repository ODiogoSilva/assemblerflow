process_spades
==============


Purpose
-------

This components processes the assembly resulting from the Spades software and,
optionally, filters contigs based on user-provide parameters.

Input/Output type
------------------

- Input type: ``Fasta``
- Output type: ``Fasta``

.. note::
    The default input parameter for fasta data is ``--fasta``.

Parameters
----------

- ``spadesMinKmerCoverage``: Minimum contigs K-mer coverage. After assembly
  only keep contigs with reported k-mer coverage equal or above this value.
- ``spadesMinContigLen``: Filter contigs for length greater or equal than
  this value.
- ``spadesMaxContigs``: Maximum number of contigs per 1.5 Mb of expected
  genome size.

Published results
-----------------

None.

Published reports
-----------------

- ``reports/assembly/spades_filter``: The filter status for each contig and
  each sample. If any contig does not pass the filters, it reports which
  filter type it failed and the corresponding value.

Default directives
------------------

- ``container``: ummidock/spades
- ``version``: 3.11.1-1

Advanced
--------

Template
^^^^^^^^

:mod:`flowcraft.templates.process_assembly`

Reports JSON
^^^^^^^^^^^^

``tableRow``:
    - ``Contigs (<assembler>)``: Number of contigs
    - ``Assembled BP (<assembler>)``: Number of assembled base pairs
``warnings``:
    - ``process_assembly``: Failure messages