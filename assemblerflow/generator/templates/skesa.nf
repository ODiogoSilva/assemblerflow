
process skesa_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { fastq_id }
    publishDir 'results/assembly/skesa_{{ pid }}', pattern: '*_skesa.assembly.fasta', mode: 'copy'

    input:
    set fastq_id, file(fastq_pair) from {{ input_channel }}

    output:
    set fastq_id, file('*.fasta') into {{ output_channel }}
    {% with task_name="skesa" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    template "skesa.py"

}