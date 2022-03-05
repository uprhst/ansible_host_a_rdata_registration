#provider.py

# Module allowing dynamic inclusion of upstream providers
# helping with server/instance management
# to be completed
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION='''
module: provider
short_description: Management module for dynamic list of upstream providers
description: Management module for dynamic list of upstream providers
options:
    name:
        description: Name of the server to be managed
        required: true
        type: str
    command:
        description: Command to supply to the provider script
        required: true
        type: str
    options:
        description: JSON Object as string with set of options to supply to the provider script
        required: true
        type: str
    provider:
        description: Upstream provider name
        required: false
        type: str
'''

import os
import json
from importlib.machinery import SourceFileLoader
from ansible.module_utils.basic import AnsibleModule

def main():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        command=dict(type='str', required=True),
        options=dict(type='str', required=True),
        provider=dict(type='str', required=False, default="vultr"),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    provider_conf = "{cwd}/upstream/{provider}/{provider}.yaml".format(cwd=os.getcwd(), provider=module.params['provider'])
    provider = "{cwd}/upstream/{provider}/{provider}.py".format(cwd=os.getcwd(), provider=module.params['provider'])

    command = module.params['command']
    options = module.params['options']

    upstream = SourceFileLoader("upstream", provider).load_module()

    upstream.mod(module, command, options, provider_conf)

    # module.exit_json(**result)
    module.fail_json(msg='Failed module execution with params: {}'.format(module.params), changed=False)

if __name__ == '__main__':
    main()