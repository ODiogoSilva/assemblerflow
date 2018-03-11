
if (params.chewbbacaToPhyloviz == true){
    jsonOpt = ""
} else {
    jsonOpt = "--json"
}

process chewbbaca {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    maxForks 1
    tag { fastq_id + " getStats" }
    scratch true
    // publishDir "results/chewbbaca/${fastq_id}"
    if (params.chewbbacaQueue != null) {
        queue '${params.chewbbacaQueue}'
    }

    input:
    set fastq_id, file(assembly) from {{ input_channel }}
    each file(schema) from Channel.fromPath(params.schemaPath)

    output:
    file 'chew_results'
    file 'results'
    {% with task_name="chewbbaca" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    when:
    params.chewbbacaRun == true

    script:
    """
    {
        if [ -d ${params.schemaPath}/temp ];
        then
            rm -r ${params.schemaPath}/temp
        fi

        echo $assembly >> input_file.txt
        chewBBACA.py AlleleCall -i input_file.txt -g ${params.schemaSelectedLoci} -o chew_results $jsonOpt --cpu $task.cpus -t "${params.chewbbacaSpecies}"
        if [ ! $jsonOpt = ""]; then
            merge_json.py ${params.schemaCore} chew_results/*/results*
        else
            chewBBACA.py RemoveGenes -i chew_results/*/results_alleles.tsv -g chew_results/*/RepeatedLoci.txt -o alleleCallMatrix_cg
            chewBBACA.py ExtractCgMLST -i alleleCallMatrix_cg.tsv -o results -p $params.chewbbacaProfilePercentage
        fi
    } || {
        echo fail > .status
    }
    """

}
