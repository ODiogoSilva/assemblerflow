// check if option file is provided or not
optionFile = (params.option_file{{ param_id }} == false) ? "" :
    "--option-file ${params.option_file{{ param_id }}}"

// process to run fasterq-dump from sra-tools
process fasterqDump_{{ pid }} {

    {% include "post.txt" ignore missing %}

    tag { accession_id }
    publishDir "reads/", pattern: "${accession_id}/*fastq.gz"
    maxRetries 1

    input:
    val accession_id from {{ input_channel }}.splitText(){ it.trim() }.filter{ it.trim() != "" }

    output:
    set accession_id, file("*fastq.gz") optional true into {{ output_channel }}
    {% with task_name="fasterqDump", sample_id="accession_id" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    """
    {
        echo "Downloading the following accession: ${accession_id}"
        echo ${params.option_file{{ param_id }}}
        fasterq-dump ${accession_id} -e ${task.cpus} -p ${optionFile}
        test -f ${accession_id}_1.fastq && gzip ${accession_id}_1.fastq \
        ${accession_id}_2.fastq || test -f ${accession_id}_3.fastq && \
        gzip ${accession_id}_3.fastq || echo "No reads were found to compress"
    } || {
        # If exit code other than 0
        if [ \$? -eq 0 ]
        then
            echo "pass" > .status
        else
            echo "fail" > .status
            echo "Could not download accession $accession_id" > .fail
        fi
    }
    """
}
