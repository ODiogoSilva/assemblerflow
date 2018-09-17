// runs fast ani for multiple comparisons (many to many mode)
process fastAniMatrix_{{ pid }} {

    {% include "post.txt" ignore missing %}

    tag { sample_id }

    input:
    set sample_id, file(fasta) from {{ input_channel }}

    output:
    set sample_id, fasta, file("*.out") into fastAniMatrixOutChannel_{{ pid }}
    {% with task_name="fastAniMatrix", sample_id="sample_id" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    """
    fastANI --ql ${sample} --rl ${fasta} \
    -o ${sample_id.take(sample_id.lastIndexOf("."))}.out
    """

}
