from __future__ import absolute_import, division, print_function

import pytest
import yaml

try:
    # ansible-test style imports
    from ansible_collections.tripleo.collect_logs.plugins.module_utils.test_utils import (
        AnsibleExitJson,
        AnsibleFailJson,
        ModuleTestCase,
        set_module_args,
    )
    from ansible_collections.tripleo.collect_logs.plugins.modules import (
        flatten_nested_dict,
    )
except ImportError:
    # avoid collection errors running: pytest --collect-only
    import os
    import sys

    plugins_path = os.path.join(os.path.dirname(__file__), "../../plugins/")
    plugins_path = os.path.realpath(plugins_path)
    sys.path.append("%s/%s" % (plugins_path, "module_utils"))
    sys.path.append("%s/%s" % (plugins_path, "modules"))
    import flatten_nested_dict
    from test_utils import (
        AnsibleExitJson,
        AnsibleFailJson,
        ModuleTestCase,
        set_module_args,
    )


__metaclass__ = type
SAMPLE_INPUT_1 = """
data:
  system:
    cpuinfo:
      cmd: cat /proc/cpuinfo
      capture_file: /var/log/extra/cpuinfo.txt
"""

SAMPLE_OUTPUT_1 = """
data:
  - cmd: cat /proc/cpuinfo
    capture_file: /var/log/extra/cpuinfo.txt
    name: cpuinfo
    group: system
"""


class TestFlattenNestedDict(ModuleTestCase):
    def test_invalid_args(self):
        set_module_args(
            data="invalid",
        )
        with pytest.raises(AnsibleFailJson) as context:
            flatten_nested_dict.main()
        assert context.value.args[0]["failed"] is True
        assert "msg" in context.value.args[0]

    def test_empty(self):
        set_module_args(
            data={},
        )
        with pytest.raises(AnsibleExitJson) as context:
            flatten_nested_dict.main()
        assert context.value.args[0] == {"data": [], "changed": False}

    def test_one(self):
        set_module_args(data=yaml.safe_load(SAMPLE_INPUT_1)["data"])
        with pytest.raises(AnsibleExitJson) as context:
            flatten_nested_dict.main()
        assert context.value.args[0]["changed"] is False
        assert context.value.args[0]["data"] == yaml.safe_load(SAMPLE_OUTPUT_1)["data"]
