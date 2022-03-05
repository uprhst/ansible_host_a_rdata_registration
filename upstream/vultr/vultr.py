import time
import yaml
import json
import requests

from jinja2 import Template
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.utils.vars import load_extra_vars

# Simple collection script,
# as this is only a showcase
# can be further extended if 
# I decide to put it in production
def collect(config):
    collected = []
    headers = {}

    # This could be perhaps optimized
    for h in config['inventory']['options']['headers']:
        key = list(h.keys())[0]
        headers[key] = h[key]

    response = {}

    # Maybe add a timeout
    if config['inventory']['options']['method'].lower() == "get":
        response = requests.get(config['inventory']['endpoint'], headers=headers)
        if response.status_code != requests.codes.ok:
            raise AnsibleError(
               'Failed fetching data from upstream: {}'.format(response.text))

    # For the time being we skip pagination and focus only on instance data
    instances = response.json()['instances'] 
    
    for _instance in instances:
        data = {}
        data['id'] = _instance['id']
        data['hostname'] = _instance['hostname']
        data['ip4'] = _instance['main_ip']
        data['ip6'] = _instance['v6_network']
        data['location'] = _instance['region']
        collected.append(data)

    return collected

# This is part of the Provider module
# here we can define multiple commands
def mod(module, command, options, provider_conf):
    command = command.lower()

    # Copied straight from the inventory plugin
    with open(provider_conf, 'r') as file:
        data = file.read();

    parsed_data = yaml.full_load(data)

    try:
        parsed_data = Template(data).render(parsed_data)
    except Exception as e:
        raise AnsibleParserError('Failed parsing provider yaml configu file: {}'.format(e))

    config = yaml.full_load(parsed_data)

    if command == "create":
        create(module, options, config)
        return
    
    module.fail_json(msg='Unrecognised command: {}'.format(command), changed=False)
        
def create(module, options, config):
    options = json.loads(options)

    data = {
        "label": module.params['name'],
        "hostname": module.params['name'],
        "enable_ipv6": True,
        "enable_private_network": True,
    }

    if not "plan" in options:
        module.fail_json(msg='Missing Create endpoint option: plan not found', changed=False)
    elif not "region" in options:
        module.fail_json(msg='Missing Create endpoint option: region not found', changed=False)

    for key in options.keys():
        data[key] = options[key]
        # print(key)

    config = config['module']
    headers = {}

    for h in config['create']['options']['headers']:
        key = list(h.keys())[0]
        headers[key] = h[key]

    # Maybe add a timeout
    if config['create']['options']['method'].lower() == "post":
        response = requests.post(config['create']['endpoint'], headers=headers, json=data)
        if response.status_code != 202:
            raise AnsibleError(
               'Failed posting data to upstream: {}'.format(response.text))

    instance = response.json()['instance']

    # At this point we successfully created the server,
    # we just need to wait long enough for it to complete
    # its setup
    while True:
        time.sleep(60)

        response = requests.get("{}/{}".format(config['get']['endpoint'], instance['id']), headers=headers)
        
        if response.status_code != requests.codes.ok:
            raise AnsibleError(
               'Failed fetching data from upstream: {}'.format(response.text))
        
        instance = response.json()['instance']

        if not instance['server_status'] == "locked":
            break;

    # And once the setup is done, we return the our data
    module.exit_json(changed=True, msg="Successfully created server `{}` with ID: {}".format(instance['hostname'], instance['id']), instance=instance)