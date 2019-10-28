Coverage_{{ pid }} = Channel.value(params.coverage{{ param_id }})

process seroba_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { sample_id }

    input:
    set sample_id, file(fastq) from {{ input_channel }}
    val coverage from Coverage_{{ pid }}

    output:
    file("*_pred.tsv") into LOG_seroba_{{ pid }}
    {% with task_name="seroba" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    """
    {
        # create a directory to store the results
        mkdir results/
        #rename input files for seroba (avoid match error)
        mv ${fastq[0]} ${sample_id}_1.fq.gz
        mv ${fastq[1]} ${sample_id}_2.fq.gz
        # run seroba typing module
        seroba runSerotyping --coverage ${coverage} /seroba/database/ ${sample_id}_1.fq.gz ${sample_id}_2.fq.gz \$PWD/results/${sample_id}

        # Get the ST for the sample
        if [ -f "\$PWD/results/${sample_id}/pred.tsv" ];
        then
            mv \$PWD/results/${sample_id}/pred.tsv ${sample_id}_pred.tsv
            sed -i -- "s|\$PWD/results/||g" ${sample_id}_pred.tsv
            # Add ST information to report JSON
            json_str="{'tableRow':[{'sample':'${sample_id}','data':[{'header':'serotype','value':'\$(cat ${sample_id}_pred.tsv | cut -f2)','table':'typing'}]}]}"
            echo \$json_str > .report.json
            rm -r results/
        else
            echo fail > .status
            rm -r results/
        fi
    } || {
        echo fail > .status
        # Remove results directory
        rm -r results/
    }
    """

}

process compile_seroba_{{ pid }} {

    publishDir "results/typing/seroba_{{ pid }}/"

    input:
    file res from LOG_seroba_{{ pid }}.collect()

    output:
    file "seroba_report.tsv"

    script:
    """
    cat ${res} >> seroba_report.tsv
    """
}

{{ forks }}