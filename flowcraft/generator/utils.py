import re

try:
    import generator.error_handling as eh
    from generator.process_details import colored_print
except ImportError:
    import flowcraft.generator.error_handling as eh
    from flowcraft.generator.process_details import colored_print


def get_nextflow_filepath(log_file, error_mode):

    with open(log_file) as fh:
        # Searches for the first occurence of the nextflow pipeline
        # file name in the .nextflow.log file
        while 1:
            line = fh.readline()
            if not line:
                # file is empty
                raise  error_mode("Nextflow command path could not be found - Is .nextflow.log empty?")
            try:
                # Regex supports absolute paths and relative paths
                pipeline_path = re.match(".*\s([/\w/]*\w*.nf).*", line) \
                    .group(1)
                return pipeline_path
            except AttributeError:
                continue