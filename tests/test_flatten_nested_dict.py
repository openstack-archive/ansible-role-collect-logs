import pytest  # noqa
import flatten_nested_dict
from common.utils import (
    AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args,
)
import yaml


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
        assert context.value.args[0]['failed'] is True
        assert 'msg' in context.value.args[0]

    def test_empty(self):
        set_module_args(
            data={},
        )
        with pytest.raises(AnsibleExitJson) as context:
            flatten_nested_dict.main()
        assert context.value.args[0] == {'data': [], 'changed': False}

    def test_one(self):
        set_module_args(
            data=yaml.safe_load(SAMPLE_INPUT_1)['data']
        )
        with pytest.raises(AnsibleExitJson) as context:
            flatten_nested_dict.main()
        assert context.value.args[0]['changed'] is False
        assert context.value.args[0]['data'] == \
            yaml.safe_load(SAMPLE_OUTPUT_1)['data']
