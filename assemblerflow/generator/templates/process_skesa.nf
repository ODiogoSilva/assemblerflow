
process process_skesa_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { fastq_id}
    // This process can only use a single CPU
    cpus 1
    publishDir "reports/assembly/skesa_filter_{{ pid }}", pattern: '*.report.csv', mode: 'copy'

    input:
    set fastq_id, file(assembly) from {{ input_channel }}
    val opts from IN_process_skesa_opts
    val gsize from IN_genome_size

    output:
    set fastq_id, file('*.assembly.fasta') optional true into {{ output_channel }}
    file '*.report.csv' optional true
    {% with task_name="process_skesa" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    template "process_assembly.py"

}

{{ forks }}