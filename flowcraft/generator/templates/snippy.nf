process snippy_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { sample_id }

    publishDir 'results/snippy_{{ pid }}/', mode: 'copy'

    input:
    set sample_id, file(fastq_pair) from {{ input_channel }}
    file params.reference

    output:
    file "${sample_id}" into OUT_snippy

    {% with task_name="phenix" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    """
    {
    snippy --cpus $params.threads \
    --prefix ${dataset_id} \
    --outdir ${dataset_id} \
    --ref ${params.reference} \
    --pe1 ${fastq_pair[0]} \
    --pe2 ${fastq_pair[1]}
    
    echo pass > .status
    } || {
        echo fail > .status
    }
    """
}

if (params.core_genome){
    process  snippy_core_{{ pid }} {
       publishDir 'results/snippy_{{ pid }}/core_genome', mode: "copy" 
               
       tag {"Generating core genome"}
               
       input:
       file snps from OUT_snippy.collect()    
       
       output:
       file("core.*")   
       
       script:
              
       """
       snippy-core --prefix core $snps
       """ 
    }
}

{{ forks }}