import requests

from ansible.errors import AnsibleError

# Simple collection script,
# as this is only a showcase
# can be further extended if 
# I decide to put it in production
def collect(config):
    collected = []
    headers = {}

    # This could be perhaps optimized
    for h in config['options']['headers']:
        key = list(h.keys())[0]
        headers[key] = h[key]

    response = {}

    # Maybe add a timeout
    if config['options']['method'].lower() == "get":
        response = requests.get(config['endpoint'], headers=headers)
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