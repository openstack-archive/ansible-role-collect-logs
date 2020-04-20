#!/usr/bin/python
# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
module: flatten_nested_dict
author:
  - "Sorin Sbarnea (@ssbarnea)"
version_added: '2.7'
short_description: Flattens a nested dictionary into a list
notes: []
description:
  - Flattens the commands nested dictionary into a list of commands.
options:
  data:
    description:
      - Nested dictionary
    required: True
    type: dict
  result:
    description:
      - List of commands to run.
    type: list
    elements: dict
"""
EXAMPLES = """
- name: Determine commands to run
  flatten_nested_dict:
    data:
      system:
        cmd: df
"""
RETURN = """
data:
    description: Commands to be executed
    returned: success
    type: list
    sample:
      - 'cmd': 'df'
        'capture_file': '/var/log/extra/df.txt'
        'name': 'df'
        'group': 'system'
"""


def main():
    result = {'data': [], 'changed': False}
    module = AnsibleModule(
        argument_spec=dict(
            data=dict(type='dict', default={}),
        ))
    try:

        for group, commands in module.params['data'].items():
            for cmd_name, cmd_dict in commands.items():
                cmd_dict['name'] = cmd_name
                cmd_dict['group'] = group
                result['data'].append(cmd_dict)

    except Exception as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
