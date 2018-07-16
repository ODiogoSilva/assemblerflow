reference_snippy_ch = IN_reference_snippy.first()

process snippy_{{ pid }} {

    // Send POST request to platform
    {% include "post.txt" ignore missing %}

    tag { sample_id }

    publishDir 'results/snippy_{{ pid }}/', mode: 'copy'

    input:
    set sample_id, file(fastq_pair) from {{ input_channel }}
    each file(reference_snippy) from reference_snippy_ch

    output:
    file "${sample_id}" into OUT_snippy

    {% with task_name="snippy" %}
    {%- include "compiler_channels.txt" ignore missing -%}
    {% endwith %}

    script:
    """
    {
    snippy --cpus $params.threads \
    --prefix ${sample_id} \
    --outdir ${sample_id} \
    --ref ${reference_snippy} \
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