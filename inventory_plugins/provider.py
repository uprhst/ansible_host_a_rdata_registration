#upstream_provider.py
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
name: provider
plugin_type: inventory
short_description: Return server inventory from defined upstream provider
description: Return Ansible inventory from upstream provider
options:
    plugin:
        description: Name of the plugin
        required: true
        choices: ['provider']
    path_to_providers:
        description: Directory location of the upstream provider configuration
        required: true
    source:
        description: The name of the provider
        required: true
'''

from importlib.machinery import SourceFileLoader
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.utils.vars import load_extra_vars
from ansible.utils.path import basedir
from ansible.module_utils._text import to_native
from ansible.module_utils.common._collections_compat import Mapping

class InventoryModule(BaseInventoryPlugin):
    NAME = 'provider'

    def verify_file(self, path):
        '''Return true/false if this file exists'''

        if super(InventoryModule, self).verify_file(path):
            return True

        return False

    def _verify(self):
        '''Verify the upstream configuration path and contents'''

        config = {}
        path = self.upstream_config_path

        # Verify the file exists
        try:
            config = self.loader.load_from_file(path, cache=False)
        except Exception as e:
            raise AnsibleError(to_native(e))

        if not config:
            raise AnsibleParserError("%s is empty" % (to_native(path)))
        elif 'endpoint' not in config:
            # Where is my Endpoint?
            raise AnsibleParserError("Endpoint location not found: %s" % config.get('endpoint', 'none found'))
        elif 'options' not in config:
            # I have no Options
            raise AnsibleParserError("No options defined: %s" % config.get('options', 'none found'))
        elif 'method' not in config['options']:
            # I do not have METHOD assigned
            raise AnsibleParserError("Endpoint access Method not defined: %s" % config.get('options').get('method', 'none found'))
        elif not isinstance(config, Mapping):
            # configs are dictionaries
            raise AnsibleParserError('inventory source has invalid structure, it should be a dictionary, got: %s' % type(config))

        return config

    def _populate(self, config):
        '''Run upstream configuration script and return hosts and groups'''
        upstream = SourceFileLoader("upstream", self.upstream_run_script_path).load_module()

        data = upstream.collect(config)

        locations = []

        # Iterate and collect locations
        # we will be using them as groups
        for _ins in data:
            if not _ins['location'] in locations:
                locations.append(_ins['location'])

        for _loc in locations:
            self.inventory.add_group(_loc)

        # Finally collect instance data
        for _ins in data:
            self.inventory.add_host(_ins['hostname'], group=_ins['location'])
            self.inventory.set_variable(_ins['hostname'], 'id', _ins['id'])
            self.inventory.set_variable(_ins['hostname'], 'ip4', _ins['ip4'])
            self.inventory.set_variable(_ins['hostname'], 'ip6', _ins['ip6'])
            self.inventory.set_variable(_ins['hostname'], 'ansible_host', _ins['ip4'])
            # self.inventory.set_variable(_ins['hostname'], 'ansible_network_os', 'ios')


    def parse(self, inventory, loader, path, cache):
        '''Return dynamic inventory from source '''

        super(InventoryModule, self).parse(inventory, loader, path, cache)
        
        self._read_config_data(path)

        try:
            # Load default YAML options
            self.plugin = self.get_option('plugin')
            self.upstream_dir = self.get_option('path_to_providers')
            self.upstream_provider = self.get_option('source')

            # Allow Upstream provider to be overriden
            # using extra variable -e source=[provider]
            # since we aim to provide support for multiple
            # providers
            self._extra_vars = load_extra_vars(loader)
            
            if 'source' in self._extra_vars:
                self.upstream_provider = self._extra_vars['source']
        except Exception as e:
            raise AnsibleParserError(
               'Missing required option/s: {}'.format(e))

        # Exit unless the upstream provider configuration file exists
        self.upstream_config_path = "{}/{}/{}/{}.yaml".format(basedir(path),self.upstream_dir, self.upstream_provider, self.upstream_provider)
        self.upstream_run_script_path = "{}/{}/{}/{}.py".format(basedir(path),self.upstream_dir, self.upstream_provider, self.upstream_provider)

        if not super(InventoryModule, self).verify_file(self.upstream_config_path):
            raise AnsibleParserError('Required upstream configuration file doesn\'t exist: {}'.format(self.upstream_config_path))
            
        if not super(InventoryModule, self).verify_file(self.upstream_run_script_path):
            raise AnsibleParserError('Required upstream run script file doesn\'t exist: {}'.format(self.upstream_run_script_path))

        config = self._verify()
        self._populate(config)
