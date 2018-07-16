reference_phenix_ch = IN_reference_phenix.first()
phenix_config_ch = IN_phenix_config.first()

process phenix_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { sample_id }

    publishDir 'results/phenix_{{ pid }}/', mode: 'copy'

    input:
    set sample_id, file(fastq_pair) from {{ input_channel }}
    each file(phenix_config) from phenix_config_ch
    each file(reference_phenix) from reference_phenix_ch

    output:
    file "${sample_id}" into OUT_phenix

    {% with task_name="phenix" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}
    
    script:
    """
    {

    phenix.py prepare_reference -r ${reference_phenix} \
    --mapper $params.mapper \
    --variant $params.variant

    phenix.py run_snp_pipeline \
    -r1 ${fastq_pair[0]} \
    -r2 ${fastq_pair[1]} \
    -r ${reference_phenix} \
    -c ${phenix_config} \
    --keep-temp \
    --json \
    --sample-name ${sample_id} \
    -o ${sample_id}

    phenix.py vcf2fasta \
    -i ${sample_id}/${sample_id}.filtered.vcf \
    -o ${sample_id}/${sample_id}_all.fasta \
    --reference ${reference_phenix} \
    --regex filtered

    # Remove reference genome
    seqkit grep -n -i -v -p "reference" ${sample_id}/${sample_id}_all.fasta > ${sample_id}/${sample_id}.fa

    # Statistics for mapped bam file
    qualimap bamqc -bam ${sample_id}/${sample_id}.bam -outdir stats

    mv stats/genome_results.txt ${sample_id}/${sample_id}_stats_cov.txt

    echo pass > .status
    } || {
        echo fail > .status
    }
    """
}

if (params.extract_snps) {
    process extract_snps_{{ pid }} {
       publishDir 'results/phenix_{{ pid }}/snps', mode: "copy" 
               
       tag {"Extracting snps"}
               
       input:
       file phenix_out from OUT_phenix.collect()
       
       output:
       file("snps.mla")  
       
       script:
              
       """
       cat */*.fa > phenix.aln
       snp-sites -o snps.mla phenix.aln       
       """  
    }
}

{{ forks }}