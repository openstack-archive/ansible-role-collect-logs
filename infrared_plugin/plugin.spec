---
# This file and main.yml are required by Infrared project
config:
  plugin_type: other
  entry_point: main.yml
  roles_path: ../
subparsers:
  ansible-role-collect-logs:
    description: An Ansible role for aggregating logs from different nodes.
    include_groups: ["Ansible options", "Common options"]
    groups:
      - title: Collecting
        options:
          openstack_nodes:
             type: Value
             help: |
               OpenStack nodes ansible-role-collect-logs will be executed on.
             default: all:!localhost
          artcl_report_server_key:
             type: Value
             help: |
               A path to a key for an access to the report server.
          artcl_rsync_path:
             type: Value
             help: |
               Specifies a server hostname and a path where the artifacts will
               be stored. Example: username@hostname:/path/to/the/dest
          artcl_collect_list:
            type: ListValue
            help: |
              A list of files and directories to gather from the target.
              Directories are collected recursively and need to end with a “/”
              to get collected. Should be specified as a YaML list, e.g.:
                infrared ansible-role-collect-logs \
                  --artcl_collect_list /etc/nova/,/home/stack/*.log,/var/log/
          artcl_collect_list_append:
            type: ListValue
            help: |
              A list of files and directories to be appended in the default
              list. This is useful for users that want to keep the original
              list and just add more relevant paths.
          artcl_exclude_list:
            type: ListValue
            help: |
              A list of files and directories to exclude from collecting. This
              list is passed to rsync as an exclude filter and it takes
              precedence over the collection list. For details see the
              “FILTER RULES” topic in the rsync man page.
          artcl_exclude_list_append:
            type: ListValue
            help: |
              A list of files and directories to be appended in the default
              exclude list. This is useful for users that want to keep the
              original list and just add more relevant paths.
          artcl_commands:
            type: NestedDict
            help: |
              Collect commands executed by the role. Keep the dict sorted.
              Example: --artcl_commands <group_type>.<command name>.cmd=<command>
              Note: group types to be collected are defined by collect_log_types
              Example2: --artcl_commands system.cpuinfo.cmd="cat /proc/cpuinfo"
          artcl_commands_extras:
            type: NestedDict
            help: |
              Commands to be executed, combined with artcl_commands.
          artcl_rsync_collect_list:
            type: Bool
            help: |
              If true, artcl_collect_list is given to rsync to collect
              logs, otherwise it is given to find to create a list of files
              to collect for rsync.
            default: True
          local_working_dir:
            type: Value
            help: |
              Destination on the executor host where the logs will be collected
              to.
            default: /tmp/collect_logs
          artcl_collect_dir:
            type: Value
            help: |
              A directory on the executor host within local_working_dir where
              the logs should be gathered, without a trailing slash.
          artcl_build_url:
            type: Value
            help: |
              Build URL used for fetching console.log
          artcl_gzip:
            type: Bool
            help: |
              When true, gathered files are gzipped one by one
              in artcl_collect_dir, when false, a tar.gz file will contain all
              the logs.
          collect_log_types:
            type: ListValue
            help: |
              A list of which type of logs will be collected, such as openstack
              logs, network logs, system logs, etc. Acceptable values are
              system, monitoring, network, openstack and container.
          artcl_collect_sosreport:
            type: Bool
            help: |
              If true, create and collect a sosreport for each host.
      - title: Publishing
        options:
          artcl_publish:
            type: Bool
            help: |
              If true, the role will attempt to rsync logs to the target
              specified by artcl_rsync_url. Uses BUILD_URL, BUILD_TAG vars from
              the environment (set during a Jenkins job run) and requires the
              next to variables to be set.
          artcl_txt_rename:
            type: Bool
            help: |
              Rename compressed text based files to end with txt.gz extension.
          artcl_readme_path:
            type: Value
            help: |
              Path to a readme file to be copied to base directory, containing
              information regarding the logs.
          artcl_readme_file:
            type: Value
            help: |
              Name of the readme file
          artcl_publish_timeout:
            type: Value
            help: |
              The maximum seconds the role can spend uploading the logs.
          artcl_use_rsync:
            type: Bool
            help: |
              If true, the role will use rsync to upload the logs.
          artcl_rsync_use_daemon:
            type: Bool
            help: |
              If true, the role will use rsync daemon instead of ssh to
              connect.
          artcl_rsync_url:
            type: Value
            help: |
              rsync target for uploading the logs. The localhost needs to have
              passwordless authentication to the target or the PROVISIONER_KEY
              var specificed in the environment.
          artcl_use_swift:
            type: Bool
            help: |
              If true, the role will use swift object storage to publish
              the logs.
          artcl_swift_auth_url:
            type: Value
            help: |
              The OpenStack auth URL for Swift.
          artcl_swift_username:
            type: Value
            help: |
              OpenStack username for Swift.
          artcl_swift_password:
            type: Value
            help: |
              Password for the Swift user.
          artcl_swift_tenant_name:
            type: Value
            help: |
              OpenStack tenant name for Swift.
          artcl_swift_container:
            type: Value
            help: |
              The name of the Swift container to use.
          artcl_swift_delete_after:
            type: Value
            help: |
              The number of seconds after which Swift will remove the uploaded
              objects.
          artcl_artifact_url:
            type: Value
            help: |
              An HTTP URL at which the uploaded logs will be accessible after
              upload.
          influxdb_create_data_file:
            type: Bool
            help: |
              Upload data to the InfluxDB database.
            default: False
          ara_enabled:
            type: Bool
            help: |
              If true, the role will generate ara reports.
          ara_generate_html:
            type: Bool
            help: |
              Whether to generate ara html or not.
            default: False
          remote_user:
            type: Value
            help: |
              Name of a remote user under which the tasks will be executed.
            default: stack
          disable_artifacts_cleanup:
            type: Bool
            help: |
                Determines whether to keep collected files
            default: False
