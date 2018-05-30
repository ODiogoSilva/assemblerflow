
process sistr_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { sample_id }
    publishDir 'results/typing/sistr_{{ pid }}'

    input:
    set sample_id, file(assembly) from {{ input_channel }}

    output:
    {% with task_name="sistr" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    """
    sistr --qc -vv -t $task.cpus -f json -o ${sample_id}_sistr.json ${assembly}
    """

}

{{ forks }}
