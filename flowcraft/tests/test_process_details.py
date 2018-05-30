import pytest

import flowcraft.generator.process_details as pd
import flowcraft.flowcraft as af

from flowcraft.generator.engine import process_map
from flowcraft.generator.process_details import COLORS


def test_color_print():

    for c in COLORS:
        pd.colored_print("teste_msg", c)

    assert 1


def test_long_list():

    arguments = af.get_args(["build", "-L"])

    with pytest.raises(SystemExit):
        pd.proc_collector(process_map, arguments)


def test_short_list():

    arguments = af.get_args(["build", "-l"])

    with pytest.raises(SystemExit):
        pd.proc_collector(process_map, arguments)
        