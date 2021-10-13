# Copyright 2021 Red Hat Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Usage:
# will use /var/log/audit/audit.log as source
# ./consolidate-avc.pl
# Will use another input
# ./consolidate-avc.pl /var/log/extras/denials.txt

use strict;
use warnings;
use List::Util qw'first';

my $logfile = shift // '/var/log/audit/audit.log';

open(AUDIT_LOG, $logfile) or die("Could not open file '${logfile}'.");

my @denials = ();
while( my $line = <AUDIT_LOG>)  {
  my @matched = $line =~ m{type=AVC.* denied  \{([\w\s]+)\}.* scontext=([\w:]+)(:[,c0-9]+)? tcontext=([\w:,]+) tclass=([\w]+) permissive=[01]};
  if (@matched) {
    my $action = $matched[0];
    my $scontext = $matched[1];
    my $tcontext = $matched[3];
    my $tclass = $matched[4];
    my $matcher = "${action}_${scontext}_${tcontext}_${tclass}";
    if (!first {$matcher eq $_} @denials) {
      push(@denials, $matcher);
      print $line;
    }
  }
}
close(AUDIT_LOG);
