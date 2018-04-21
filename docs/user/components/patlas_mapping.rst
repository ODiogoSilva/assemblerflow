pATLAS mapping
==============

Purpose
-------

This component aims to produce to be a mapping approach to find plasmids
contained in high throughoput sequencing data. Then, the resulting file can
be imported into .. _pATLAS: http://www.patlas.site/ .

.. note::
    pATLAs software documentation can be found .. _here: https://tiagofilipe12.gitbooks.io/patlas/content/


Input/Output type
------------------

- Input type: ``FastQ``
- Output type: ``JSON``


Parameters
----------

- `max_k`: Sets the k parameter for bowtie2 allowing to make multiple mappings
of the same read against several hits on the query sequence or sequences.
Default: 10949.

- `trim5`: Sets trim5 option for bowtie. This will become legacy with QC
integration, but it enables to trim 5' end of reads to be mapped with bowtie2.
Default: 0

- `lengthJson`: A dictionary of all the lengths of reference sequences.
Default: 'jsons/*_length.json' (from docker image).

- `refIndex`: Specifies the reference indexes to be provided to bowtie2.
Default: '/ngstools/data/indexes/bowtie2idx/bowtie2.idx' (from docker image).

- `samtoolsIndex`: Specifies the reference indexes to be provided to samtools.
Default: '/ngstools/data/indexes/fasta/samtools.fasta.fai' (from docker image).


Published results
-----------------

- ``results/mapping/``: A `JSON` file that can be imported to .. _pATLAS: http://www.patlas.site/
with the results from mapping.


Published reports
-----------------

None.


Default directives
------------------

- ``mappingBowtie``:
    - ``container``: tiagofilipe12/patlasflow_mapping
    - ``version``: 1.1.2
- ``samtoolsView``:
    - ``container``: tiagofilipe12/patlasflow_mapping
    - ``version``: 1.1.2
- ``jsonDumpingMapping``:
    - ``container``: tiagofilipe12/patlasflow_mapping
    - ``version``: 1.1.2


Advanced
--------

Template
^^^^^^^^

:mod:`assemblerflow.templates.patlas_mapping`


Reports JSON
^^^^^^^^^^^^

None.