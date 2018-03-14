
process mlst {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { fastq_id + " getStats" }
    // This process can only use a single CPU
    cpus 1

    input:
    set fastq_id, file(assembly) from {{ input_channel }}

    output:
    file '*.mlst.txt' into LOG_mlst_{{ pid }}
    set fastq_id, file(assembly), file(".status") into MAIN_mlst_out_{{ pid }}
    {% with task_name="mlst" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    when:
    params.mlstRun  == true && params.annotationRun

    script:
    """
    {
        expectedSpecies=${params.mlstSpecies}
        mlst $assembly >> ${fastq_id}.mlst.txt
        mlstSpecies=\$(cat *.mlst.txt | cut -f2)
        json_str="{'expectedSpecies':\'$expectedSpecies\','species':'\$mlstSpecies','st':'\$(cat *.mlst.txt | cut -f3)'}"
        echo \$json_str > .report.json

        if [ ! \$mlstSpecies = $expectedSpecies ];
        then
            printf fail > .status
        else
            printf pass > .status
        fi

    } || {
        printf fail > .status
    }
    """
}

process compile_mlst {

    publishDir "results/annotation/mlst_{{ pid }}/"

    input:
    file res from LOG_mlst_{{ pid }}.collect()

    output:
    file "mlst_report.tsv"

    when:
    params.mlstRun == true && params.annotationRun

    script:
    """
    cat $res >> mlst_report.tsv
    """
}

{{ output_channel }} = Channel.create()
MAIN_mlst_out_{{ pid }}
    .filter{ it[2].text != "fail" }
    .map{ [it[0], it[1]] }
    .set{ {{output_channel}} }


{{ forks }}

