import pytest
import os

import flowcraft.generator.utils as utils
from flowcraft.generator.error_handling import InspectionError


def test_empty_log():
    with pytest.raises(InspectionError):
        utils.get_nextflow_filepath(
            os.path.join(os.getcwd(), "tests/broadcast_tests/empty_log.txt"),
            InspectionError
        )


def test_no_path_in_log():
    with pytest.raises(InspectionError):
        utils.get_nextflow_filepath(
            os.path.join(os.getcwd(), "tests/broadcast_tests/log_without_command.txt"),
            InspectionError
        )


def test_path_in_log():
    filepath = utils.get_nextflow_filepath(
        os.path.join(os.getcwd(), "tests/broadcast_tests/log_with_command.txt"),
        InspectionError
    )

    assert filepath != ""
