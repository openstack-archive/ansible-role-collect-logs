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


ANSIBLE_METADATA = {
    "metadata_version": "0.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
module: sova
author: Sagi Shnaidman (@sshnaidm)
version_added: '2.7.0'
short_description: Parse CI jobs files for known failures
notes: []
description:
  - Parse CI job files and find there known patterns of failures
requirements:
  - "Better to use with 'regex' module installed"
options:
  files:
    description:
      - Dictionary of patterns file name and file location.
        Patterns are divided by sections in config file, match each section
        to the file path on the host, It will search these patterns from this
        section in the given file.
    required: True
    type: dict
  result:
    description:
      - Path to file where to write result message.
    type: path
  result_file_dir:
    description:
      - Directory where to create a file with result message and name
        of file. For example for pattern 'Overcloud failed on host' will be
        created file Overcloud_failed_on_host.log in this directory.
        It helps to know what is the reason without opening actually the file.
    type: path
  config:
    description: config
    type: dict
"""
EXAMPLES = """
- name: Run sova task
  sova:
    files:
      console: /var/log/job-output.txt.gz
      errors: /var/log/errors.txt.txt.gz
      "ironic-conductor": /var/log/ironic-conductor.log.txt.gz
      syslog: /var/log/journal.txt.gz
      logstash: /var/log/logstash.txt.gz
      bmc: /var/log/bmc-console.log
    result: /home/zuul/result_file
    result_file_dir: /home/zuul/workspace/logs/
"""
RETURN = """
processed_files:
    description:
      - Files which have been processed by module
    returned: if changed
    type: list
    sample: [
        "/tmp/var/log/job-output.txt.gz",
        "/tmp/var/log/errors.txt.txt.gz",
        "/tmp/var/log/ironic-conductor.log.txt.gz"
        ]
message:
    description:
      - Text with all messages about failures
    returned: if changed
    type: list
    sample: 'Overcloud stack: FAILED.'
tags:
    description:
      - Tags of patterns which were found in files
    returned: if changed
    type: list
    sample: ["info"]
file_name_written:
    description:
      - Path of file which written with message as filename
    returned: if changed
    type: str
    sample: '/var/log/_Overcloud_stack__FAILED.log'
file_written:
    description:
      - Path of file where written result message and reason.
    returned: if changed
    type: str
    sample: '/var/log/result_file'
"""

import gzip  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
from copy import deepcopy  # noqa: E402

from ansible.module_utils.basic import AnsibleModule  # noqa: E402

try:
    import regex as regex_module
except ImportError:
    import re as regex_module


__metaclass__ = type
logging.basicConfig(
    format=(
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )
)
log = logging.getLogger("parser")
log.setLevel(logging.ERROR)


class Pattern(object):
    def __init__(self, data):
        self.data = data
        self.load_yaml()
        self.setup_regexes()
        self.setup_patterns()

    def load_yaml(self):
        import yaml

        if isinstance(self.data, dict):
            self.config = self.data
        else:
            self.config = yaml.safe_load(self.data)

    def setup_regexes(self):
        self.regexes = {}
        if self.config:
            for regexp in self.config.get("regexes", []):
                flags = []
                if regexp.get("multiline"):
                    flags.append(regex_module.MULTILINE)
                self.regexes[regexp.get("name")] = regex_module.compile(
                    r"{0}".format(regexp.get("regex")), *flags
                )

    def setup_patterns(self):
        self._patterns = self.config.get("patterns", {})
        if self._patterns:
            for key in self._patterns:
                for p in self._patterns[key]:
                    if p["pattern"] in self.regexes:
                        p["pattern"] = self.regexes[p["pattern"]]
                    if p["logstash"] in self.regexes:
                        p["logstash"] = self.regexes[p["logstash"]]

    @property
    def patterns(self):
        return self._patterns


def line_match(pat, line, exclude=None):
    if isinstance(pat, str):
        return pat in line
    found = pat.search(line)
    if not found:
        return False
    if found.groups():
        if exclude:
            if any([i in found.group(1) for i in exclude]):
                return False
        return found.group(1)
    return True


def parse(text_file, patterns):
    ids = []
    msgs = []
    if text_file.split(".")[-1] == "gz":
        open_func = gzip.open
    else:
        open_func = open
    with open_func(text_file, "rt") as finput:
        text = finput.read()
        for p in patterns:
            line_matched = line_match(p["pattern"], text, exclude=p.get("exclude"))
            if line_matched:
                log.debug("Found pattern %s in file %s", repr(p), text_file)
                ids.append(p["id"])
                msgs.append(p["msg"].format(line_matched))
    return list(set(ids)), list(set(msgs))


def format_msg_filename(text):
    for s in (
        " ",
        ":",
        ".",
        "/",
        ",",
        "'",
    ):
        text = text.replace(s, "_")
    return "_" + text.rstrip("_") + ".log"


def main():

    module = AnsibleModule(
        argument_spec=dict(
            config=dict(type="dict", default={}),
            files=dict(type="dict", required=True),
            result=dict(type="path"),
            result_file_dir=dict(type="path"),
        )
    )
    if not module.params["files"]:
        module.fail_json(msg="Files for logs parsing have to be provided!")
    existing_files = []
    for pattern_file in module.params["files"]:
        file_ = module.params["files"][pattern_file]
        if os.path.exists(file_):
            existing_files.append(file_)
    if not existing_files:
        results = {"processed_files": [], "changed": False}
        module.exit_json(**results)
    dict_patterns = deepcopy(module.params["config"])

    pattern = Pattern(dict_patterns)
    PATTERNS = pattern.patterns
    for name in module.params["files"]:
        if name not in PATTERNS:
            module.fail_json(
                msg="File name %s wasn't found in [%s]"
                % (name, ", ".join(list(PATTERNS.keys())))
            )

    messages, tags = [], []
    for name, file_ in module.params["files"].items():
        if module.params["files"][name] not in existing_files:
            continue
        ids, msgs = parse(file_, PATTERNS[name])
        found = [i for i in PATTERNS[name] if i["id"] in ids]
        msg_tags = [i["tag"] for i in found if i.get("tag")]
        messages += msgs
        tags += msg_tags
    messages = list(set(messages))
    tags = list(set(tags))
    if "infra" in tags:
        reason = "infra"
    elif "code" in tags:
        reason = "code"
    else:
        reason = "unknown"
    text = " ".join(messages) or "No failure reason found"
    file_name = format_msg_filename(text)
    result = {"changed": True, "processed_files": existing_files}
    result.update({"message": text})
    result.update({"tags": tags})
    if module.params["result"] and messages:
        try:
            with open(module.params["result"], "w") as f:
                f.write(text + "\n")
                f.write("Reason: " + reason + "\n")
            result.update({"file_written": module.params["result"]})
        except Exception as e:
            module.fail_json(
                msg="Can't write result to file %s: %s"
                % (module.params["result"], str(e))
            )
    if module.params["result_file_dir"]:
        log_file = os.path.join(module.params["result_file_dir"], file_name)
        try:
            with open(log_file, "w") as f:
                f.write(text + "\n")
                f.write("Reason: " + reason + "\n")
            result.update({"file_name_written": log_file})
        except Exception as e:
            module.fail_json(
                msg="Can't write result to file %s: %s" % (log_file, str(e))
            )
    module.exit_json(**result)


if __name__ == "__main__":
    main()
