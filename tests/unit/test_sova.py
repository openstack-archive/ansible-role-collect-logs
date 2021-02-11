from __future__ import absolute_import, division, print_function

import pytest

try:
    # ansible-test style imports
    from ansible_collections.tripleo.collect_logs.plugins.module_utils.test_utils import (
        AnsibleExitJson,
        AnsibleFailJson,
        ModuleTestCase,
        set_module_args,
    )
    from ansible_collections.tripleo.collect_logs.plugins.modules import sova
except ImportError:
    # avoid collection errors running: pytest --collect-only
    import os
    import sys

    plugins_path = os.path.join(os.path.dirname(__file__), "../../plugins/")
    plugins_path = os.path.realpath(plugins_path)
    sys.path.append("%s/%s" % (plugins_path, "module_utils"))
    sys.path.append("%s/%s" % (plugins_path, "modules"))
    import sova
    from test_utils import (
        AnsibleExitJson,
        AnsibleFailJson,
        ModuleTestCase,
        set_module_args,
    )

__metaclass__ = type


class TestFlattenNestedDict(ModuleTestCase):
    def test_invalid_args(self):
        set_module_args(
            data="invalid",
        )
        with pytest.raises(AnsibleFailJson) as context:
            sova.main()
        assert context.value.args[0]["failed"] is True
        assert "msg" in context.value.args[0]

    def test_min(self):
        set_module_args(
            # just a file that exists on almost any platform
            config={
                "regexes": [{"regex": "127.0.0.1", "name": "hosts"}],
                "patterns": {
                    "console": [
                        {
                            "id": 1,
                            "logstash": "",
                            "msg": "Overcloud stack installation: SUCCESS.",
                            "pattern": "Stack overcloud CREATE_COMPLETE",
                            "tag": "info",
                        }
                    ]
                },
            },
            files={"console": "/etc/hosts"},
        )
        with pytest.raises(AnsibleExitJson) as context:
            sova.main()
        assert context.value.args[0]["changed"] is True
        assert context.value.args[0]["processed_files"] == ["/etc/hosts"]
        assert "message" in context.value.args[0]
        assert context.value.args[0]["tags"] == []
