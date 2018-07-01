process phenix_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { sample_id }

    publishDir 'results/phenix_{{ pid }}/', mode: 'copy'

    input:
    set sample_id, file(fastq_pair) from {{ input_channel }}
    file params.phenix_config
    file params.reference

    output:
    file "${sample_id}"

    {% with task_name="phenix" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    """
    {
    phenix.py prepare_reference -r $fasta \
    --mapper bwa \
    --variant gatk

    phenix.py run_snp_pipeline \
    -r1 $fastq_pair[0] \
    -r2 $fastq_pair[1] \
    -r ${fasta} \
    -c ${params.phenix_config} \
    --keep-temp \
    --json \
    --sample-name ${sample_id} \
    -o ${sample_id}

    phenix.py vcf2fasta \
    -i ${sample_id}/${sample_id}.filtered.vcf \
    -o ${sample_id}/${sample_id}_all.fasta \
    --reference ${fasta} \
    --regex filtered

    # Remove reference genome
    # seqkit grep -n -i -v -p "reference" ${sample_id}/${sample_id}_all.fasta > ${sample_id}/${sample_id}.fasta

    # Statistics for mapped bam file
    # qualimap bamqc -bam ${sample_id}/${sample_id}.bam -outdir stats

    # mv stats/genome_results.txt ${sample_id}/${sample_id}_stats_cov.txt }

    echo pass > .status
    || {
        echo fail > .status
    }
    """
}

{{ forks }}