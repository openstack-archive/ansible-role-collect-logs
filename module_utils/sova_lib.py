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

import gzip
import logging
import yaml

try:
    import regex as regex_module
except ImportError:
    import re as regex_module


logging.basicConfig(
    format=('%(asctime)s - %(name)s - %(levelname)s - '
            '%(module)s.%(funcName)s:%(lineno)d - %(message)s'))
log = logging.getLogger('parser')
log.setLevel(logging.ERROR)


class Pattern(object):
    def __init__(self, data):
        self.data = data
        self.load_yaml()
        self.setup_regexes()
        self.setup_patterns()

    def load_yaml(self):
        if isinstance(self.data, dict):
            self.config = self.data
        else:
            self.config = yaml.safe_load(self.data)

    def setup_regexes(self):
        self.regexes = {}
        if self.config:
            for regexp in self.config.get('regexes', []):
                flags = []
                if regexp.get('multiline'):
                    flags.append(regex_module.MULTILINE)
                self.regexes[regexp.get('name')] = regex_module.compile(
                    r'{}'.format(regexp.get('regex')), *flags)

    def setup_patterns(self):
        self._patterns = self.config.get('patterns', {})
        if self._patterns:
            for key in self._patterns:
                for p in self._patterns[key]:
                    if p['pattern'] in self.regexes:
                        p['pattern'] = self.regexes[p['pattern']]
                    if p['logstash'] in self.regexes:
                        p['logstash'] = self.regexes[p['logstash']]

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
            line_matched = line_match(
                p["pattern"], text, exclude=p.get("exclude"))
            if line_matched:
                log.debug("Found pattern {} in file {}".format(
                    repr(p), text_file))
                ids.append(p["id"])
                msgs.append(p["msg"].format(line_matched))
    return list(set(ids)), list(set(msgs))
