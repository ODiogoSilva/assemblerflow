// checks if cutoff value is higher than 0
if (Float.parseFloat(params.cov_cutoff.toString()) == 0) {
    exit 1, "Cutoff value of 0 will output every plasmid in the database with coverage 0. Provide a value higher than 0."
}

// process that runs bowtie2
process mappingBowtie_{{ pid }} {

    {% include "post.txt" ignore missing %}

    tag { sample_id }

    input:
    set sample_id, file(reads) from {{ input_channel }}
    val bowtie2Index from IN_index_files
    val samtoolsIdx from IN_samtools_indexes

    output:
    set sample_id, file("samtoolsDepthOutput*.txt") into samtoolsResults
    {% with task_name="mappingBowtie" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:

    //if (params.singleEnd == true) {
    //    readsString = "-U ${reads}"
    //}
    //else {
    readsString = "-1 ${reads[0]} -2 ${reads[1]}"
    //}

    """
    bowtie2 -x ${bowtie2Index} ${readsString} -p ${task.cpus} -a -5 ${params.trim5} | \
    samtools view -b -t ${samtoolsIdx} -@ ${task.cpus} - | \
    samtools sort -@ ${task.cpus} -o samtoolsSorted_${sample_id}.bam
    samtools index samtoolsSorted_${sample_id}.bam
    samtools depth samtoolsSorted_${sample_id}.bam > \
    samtoolsDepthOutput_${sample_id}.txt
    rm samtoolsDepthOutput_${sample_id}.txt samtoolsSorted_${sample_id}.bam*
    """
}

/**
* These dumping process parses the depth file for each sample and filters it
* depending on the cutoff set by the user.
*/
process jsonDumpingMapping_{{ pid }} {

    {% include "post.txt" ignore missing %}

    tag { sample_id }

    publishDir 'results/mapping/mapping_json_{{ pid }}/'

    input:
    set sample_id, file(depthFile) from samtoolsResults
    val lengthJson from IN_length_json

    output:
    set sample_id, file("samtoolsDepthOutput*.txt_mapping.json") optional true into mappingOutputChannel_{{ pid }}
    {% with task_name="jsonDumpingMapping", sample_id="sample_id" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    template "mapping2json.py"
}

{{ forks }}