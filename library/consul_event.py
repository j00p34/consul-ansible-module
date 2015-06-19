#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Chavez <chavez@somewhere-cool.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import json
import string

from collections import OrderedDict

DOCUMENTATION = '''
---
module: consul_events
version_added: "1.9"
author: Chavez
short_description: Interact with Consul Event API
description:
   - Use Consul Event API in your playbooks and roles
options:
  action:
    description:
      - One of [leader, peers]
    required: true
  dc:
    desription:
      - The datacenter to use
    required: false
    default: dc1
  host:
    description:
      - Consul host
    required: true
    default: 127.0.0.1
  name:
    description:
      - Name of event to fire
    required: false
  node:
    description:
      - Node query filter for event fire
    required: false
  port:
    description:
      - Consul API port
    required: true
  service:
    description:
      - Service query filter for event fire
    required: false
  tag:
    description:
      - Tag query filter for event fire
    required: false
  version:
    description:
      - Consul API version
    required: true
    default: v1

# informational: requirements for nodes
requirements: [ urllib, urllib2 ]
'''

EXAMPLES = '''
# Get leader
- consul_event: action=leader

# Get peers
- consul_event: action=peers
'''

#
# Module execution.
#


class ConsulEvent(object):

    ALLOWED_ACTIONS = ['fire', 'list']
    FIRE, LIST = ALLOWED_ACTIONS
    FIRE_PARAMS = ['node', 'service', 'tag']

    def __init__(self, module):
        """Takes an AnsibleModule object to set up Consul Event interaction"""
        self.module = module
        self.action = string.lower(module.params.get('action', ''))
        self.dc = module.params.get('dc', 'dc1')
        self.host = module.params.get('host', '127.0.0.1')
        self.port = module.params.get('port', 8500)
        self.version = module.params.get('version', 'v1')
        self.name = module.params.get('name', '')
        self._build_url()

    def run_cmd(self):
        self._make_api_call()

    def validate(self):
        # Check action is allowed
        if not self.action or self.action not in self.ALLOWED_ACTIONS:
            self.module.fail_json(msg='Action is required and must be one of %r' % self.ALLOWED_ACTIONS)
        # Validate action being used
        # ie self._validate_list(), self._validate_fire()
        getattr(self, "_validate_%s" % self.action)

    def _build_url(self):
        self.api_url = "http://%s:%s/%s/event/%s" % (self.host, self.port, self.version, self.action)
        if self.action in [self.FIRE]:
            self.api_url += '/%s' % self.name

    def _make_api_call(self):
        req = self._setup_request()

        try:
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            response = opener.open(req)
        except urllib2.URLError, e:
            self.module.fail_json(msg="API call (%s) failed: %s" % (self.api_url, str(e)))

        response_body = response.read()
        self._handle_response(response, response_body)

    def _setup_request(self):
        # Add dc param if not the default
        if self.dc != 'dc1':
            self.api_url = self.api_url + '?dc=%s' % self.dc

        req = urllib2.Request(url=self.api_url)
        if self.action in [self.FIRE]:
            req = urllib2.Request(url=self.api_url, data='')
            req.get_method = lambda: 'PUT'
        return req

    def _handle_response(self, response, response_body):
        code = response.getcode()
        if code != 200:
            self.module.fail_json(msg="Failed with code %i and response %s" % (code, response_body))
        else:
            try:
                parsed_response = json.loads(response_body)
            except:
                parsed_response = ''
            self.module.exit_json(changed=True, succeeded=True, value=parsed_response)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True),
            dc=dict(required=False, default='dc1'),
            host=dict(required=False, default='127.0.0.1'),
            name=dict(required=False, default=''),
            node=dict(required=False, default=''),
            port=dict(require=False, default=8500),
            service=dict(required=False, default=''),
            tag=dict(required=False, default=''),
            version=dict(required=False, default='v1'),
        ),
        supports_check_mode=True
    )

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=False)

    consul_status = ConsulEvent(module)
    consul_status.run_cmd()


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
