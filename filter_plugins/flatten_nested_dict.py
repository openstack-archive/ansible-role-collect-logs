#!/usr/bin/python


def flatten_nested_dict(v):
    r = []
    for group, commands in v.items():
        for cmd_name, cmd_dict in commands.items():
            cmd_dict['name'] = cmd_name
            cmd_dict['group'] = group
            r.append(cmd_dict)
    return r


class FilterModule(object):
    def filters(self):
        return {'flatten_nested_dict': flatten_nested_dict}
