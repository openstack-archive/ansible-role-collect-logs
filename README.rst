collect-logs
============

Ansible role for aggregating logs from different nodes.

The only supported way to call this role is using its main entry point. Do not
use ``tasks_from`` as this count as using private interfaces.

Requirements
------------

This role gathers logs and debug information from a target system and
collates them in a designated directory, ``artcl_collect_dir``, on the
localhost.

Additionally, the role will convert templated bash scripts, created and
used by TripleO-Quickstart during deployment, into rST files. These rST
files are combined with static rST files and fed into Sphinx to create
user friendly post-build-documentation specific to an original
deployment.

Finally, the role optionally handles uploading these logs to a rsync
server or to an OpenStack Swift object storage. Logs from Swift can be
exposed with
`os-loganalyze <https://github.com/openstack-infra/os-loganalyze>`__.

Role Variables
--------------

File Collection
~~~~~~~~~~~~~~~

-  ``artcl_collect_list`` – A list of files and directories to gather
   from the target. Directories are collected recursively and need to
   end with a “/” to get collected. Should be specified as a YaML list,
   e.g.:

.. code:: yaml

   artcl_collect_list:
       - /etc/nova/
       - /home/stack/*.log
       - /var/log/

-  ``artcl_collect_list_append`` – A list of files and directories to be
   appended in the default list. This is useful for users that want to
   keep the original list and just add more relevant paths.
-  ``artcl_exclude_list`` – A list of files and directories to exclude
   from collecting. This list is passed to rsync as an exclude filter
   and it takes precedence over the collection list. For details see the
   “FILTER RULES” topic in the rsync man page.
-  ``artcl_exclude_list_append`` – A list of files and directories to be
   appended in the default exclude list. This is useful for users that want to
   keep the original list and just add more relevant paths.
-  ``artcl_collect_dir`` – A local directory where the logs should be
   gathered, without a trailing slash.
-  ``collect_log_types`` - A list of which type of logs will be collected,
   such as openstack logs, network logs, system logs, etc.
   Acceptable values are system, monitoring, network, openstack and container.
-  ``artcl_gzip``: Archive files, disabled by default.
-  ``artcl_rsync_collect_list`` - if true, a rsync filter file is generated for
   ``rsync`` to collect files, if false, ``find`` is used to generate list
   of files to collect for ``rsync``. ``find`` brings some benefits like
   searching for files in a certain depth (``artcl_find_maxdepth``) or up to
   certain size (``artcl_find_max_size``).
-  ``artcl_find_maxdepth`` - Number of levels of directories below the starting
   points, default is 4. Note: this variable is applied only when
   ``artcl_rsync_collect_list`` is set to false.
-  ``artcl_find_max_size`` - Max size of a file in MBs to be included in find
   search, default value is 256. Note: this variable is applied only when
   ``artcl_rsync_collect_list`` is set to false.

-  ``artcl_commands_extras`` - A nested dictionary of additional commands to be
   run during collection. First level contains the group type, as defined by
   ``collect_log_types`` list which determines which groups are collected and
   which ones are skipped.

   Defined keys will override implicit ones from defaults
   ``artcl_commands`` which is not expected to be changed by user.

   Second level keys are used to uniqly identify a command and determine the
   default output filename, unless is mentioned via ``capture_file`` property.

   ``cmd`` contains the shell command that would be run.

.. code:: yaml

   artcl_commands_extras:
     system:
       disk-space:
         cmd: df
         # will save output to /var/log/extras/dist-space.log
       mounts:
         cmd: mount -a
         capture_file: /mounts.txt  # <-- custom capture file location
     openstack:
       key2:
         cmd: touch /foo.txt
         capture_disable: true # <-- disable implicit std redirection
         when: "1 > 2"  # <-- optional condition

Documentation generation related
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``artcl_gen_docs``: false/true – If true, the role will use build
   artifacts and Sphinx and produce user friendly documentation
   (default: false)
-  ``artcl_docs_source_dir`` – a local directory that serves as the
   Sphinx source directory.
-  ``artcl_docs_build_dir`` – A local directory that serves as the
   Sphinx build output directory.
-  ``artcl_create_docs_payload`` – Dictionary of lists that direct what
   and how to construct documentation.

   -  ``included_deployment_scripts`` – List of templated bash scripts
      to be converted to rST files.
   -  ``included_deployment_scripts`` – List of static rST files that
      will be included in the output documentation.
   -  ``table_of_contents`` – List that defines the order in which rST
      files will be laid out in the output documentation.

-  ``artcl_verify_sphinx_build`` – false/true – If true, verify items
   defined in ``artcl_create_docs_payload.table_of_contents`` exist in
   sphinx generated index.html (default: false)

.. code:: yaml

   artcl_create_docs_payload:
     included_deployment_scripts:
       - undercloud-install
       - undercloud-post-install
     included_static_docs:
       - env-setup-virt
     table_of_contents:
       - env-setup-virt
       - undercloud-install
       - undercloud-post-install

Publishing related
~~~~~~~~~~~~~~~~~~

-  ``artcl_publish``: true/false – If true, the role will attempt to
   rsync logs to the target specified by ``artcl_rsync_url``. Uses
   ``BUILD_URL``, ``BUILD_TAG`` vars from the environment (set during a
   Jenkins job run) and requires the next to variables to be set.
-  ``artcl_txt_rename``: false/true – rename text based file to end in
   .txt.gz to make upstream log servers display them in the browser
   instead of offering them to download
-  ``artcl_publish_timeout``: the maximum seconds the role can spend
   uploading the logs, the default is 1800 (30 minutes)
-  ``artcl_use_rsync``: false/true – use rsync to upload the logs
-  ``artcl_rsync_use_daemon``: false/true – use rsync daemon instead of
   ssh to connect
-  ``artcl_rsync_url`` – rsync target for uploading the logs. The
   localhost needs to have passwordless authentication to the target or
   the ``PROVISIONER_KEY`` var specified in the environment.
-  ``artcl_use_swift``: false/true – use swift object storage to publish
   the logs
-  ``artcl_swift_auth_url`` – the OpenStack auth URL for Swift
-  ``artcl_swift_username`` – OpenStack username for Swift
-  ``artcl_swift_password`` – password for the Swift user
-  ``artcl_swift_tenant_name`` – OpenStack tenant (project) name for Swift
-  ``artcl_swift_container`` – the name of the Swift container to use,
   default is ``logs``
-  ``artcl_swift_delete_after`` – The number of seconds after which
   Swift will remove the uploaded objects, the default is 2678400
   seconds = 31 days.
-  ``artcl_artifact_url`` – An HTTP URL at which the uploaded logs will
   be accessible after upload.
-  ``artcl_report_server_key`` - A path to a key for an access to the report
   server.


Ara related
~~~~~~~~~~~

- ``ara_enabled``: true/false - If true, the role will generate ara reports.
- ``ara_overcloud_db_path``: Path to ara overcloud path (tripleo only).
- ``ara_generate_html``: true/false - Generate ara html.
- ``ara_graphite_prefix``: Ara prefix to be used in graphite.
- ``ara_only_successful_tasks``: true/false - Send to graphite only successfull
  tasks.
- ``ara_tasks_map``: Dictionary with ara tasks to be mapped on graphite.

Logs parsing
~~~~~~~~~~~~
"Sova" module parses logs for known patterns and returns messages that were
found. Patterns are tagged by issues types, like "infra", "code", etc.
Patterns are located in file sova-patterns.yml in vars/ directory.

-  ``config`` - patterns loaded from file
-  ``files`` - files and patterns sections match
-  ``result`` - path to file to write a result of parsing
-  ``result_file_dir`` - directory to write a file with patterns in name

Example of usage of "sova" module:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: yaml

   ---
   - name: Run sova task
     sova:
       config: "{{ pattern_config }}"
       files:
         console: "{{ ansible_user_dir }}/workspace/logs/quickstart_install.log"
         errors: "/var/log/errors.txt"
         "ironic-conductor": "/var/log/containers/ironic/ironic-conductor.log"
         syslog: "/var/log/journal.txt"
         logstash: "/var/log/extra/logstash.txt"
       result: "{{ ansible_user_dir }}/workspace/logs/failures_file"
       result_file_dir: "{{ ansible_user_dir }}/workspace/logs"


Example Role Playbook
---------------------

.. code:: yaml

   ---
   - name: Gather logs
     hosts: all:!localhost
     roles:
       - collect-logs

** Note:
  The tasks that collect data from the nodes are executed with ignore_errors.
  For `example:  <https://opendev.org/openstack/ansible-role-collect-logs/src/branch/master/tasks/collect/system.yml#L3>`__

Templated Bash to rST Conversion Notes
--------------------------------------

Templated bash scripts used during deployment are converted to rST files
during the ``create-docs`` portion of the role’s call. Shell scripts are
fed into an awk script and output as restructured text. The awk script
has several simple rules:

1. Only lines between ``### ---start_docs`` and ``### ---stop_docs``
   will be parsed.
2. Lines containing ``# nodoc`` will be excluded.
3. Lines containing ``## ::`` indicate subsequent lines should be
   formatted as code blocks
4. Other lines beginning with ``## <anything else>`` will have the
   prepended ``##`` removed. This is how and where general rST
   formatting is added.
5. All other lines, including shell comments, will be indented by four
   spaces.


Enabling sosreport Collection
-----------------------------

`sosreport <https://github.com/sosreport/sos>`__ is a unified tool for
collecting system logs and other debug information. To enable creation
of sosreport(s) with this role, create a custom config (you can use
centosci-logs.yml as a template) and ensure that
``artcl_collect_sosreport: true`` is set.


Sanitizing Log Strings
----------------------

Logs can contain senstive data such as private links and access
passwords. The 'collect' task provides an option to replace
private strings with sanitized strings to protect private data.

The 'sanitize_log_strings' task makes use of the Ansible 'replace'
module and is enabled by defining a ``sanitize_lines``
variable as shown in the example below:

.. code:: yaml

   ---
   sanitize_lines:
     - dir_path: '/tmp/{{ inventory_hostname }}/etc/repos/'
       file_pattern: '*'
       orig_string: '^(.*)download(.*)$'
       sanitized_string: 'SANITIZED_STR_download'
     - dir_path: '/tmp/{{ inventory_hostname }}/home/zuul/'
       file_pattern: '*'
       orig_string: '^(.*)my_private_host\.com(.*)$'
       sanitized_string: 'SANITIZED_STR_host'


The task searches for files containing the sensitive strings
(orig_string) within a file path, and then replaces the sensitive
strings in those files with the sanitized_string.


Usage with InfraRed
-------------------

Run the following steps to execute the role with
`infrared <https://infrared.readthedocs.io/en/latest/>`__.

1. Install infrared and add ansible-role-collect-logs plugin by providing
   the url to this repo:

   .. code-block::

       (infrared)$ ir plugin add https://opendev.org/openstack/ansible-role-collect-logs.git --src-path infrared_plugin

2. Verify that the plugin is imported by:

   .. code-block::

       (infrared)$ ir plugin list

3. Run the plugin:

   .. code-block::

        (infrared)$ ir ansible-role-collect-logs

License
-------

Apache 2.0

Author Information
------------------

RDO-CI Team
