A showcase Ansible playbook, custom inventory plugin and an ansible module, which should allow one to manage instances from multiple upstream providers.

## Requirements
1. Python3 + pip + libffi-dev(el)
2. Ansible
3. dnsimple-python
4. requests-pyhton

Install python requirements using:
```bash
pip install -r requirements.txt
```

Run with:
```bash
ansible-playbook -i upstream_provider_inventory.yaml update_a_records.yaml
```

If additional provider is installed, you can override the default with:
```bash
ansible-playbook -i upstream_provider_inventory.yaml update_a_records.yaml -e source=do
```

## How it works
Providers consist of simple configuration file accompanied by a python script.

Directory structure should be:
```bash
|-- upstream
|   `-- vultr
|       |-- vultr.py
|       `-- vultr.yaml
```

Module API usage, it is not the best, but it is slowly coming together:
```yaml
- name: Create the server
  provider:
    name: "{{ name }}"
    command: create
    options: "{\"plan\":\"vc2-1c-1gb\",\"region\":\"fra\",\"attach_private_network\":[\"62f298c4-8e88-4d7e-bb06-141d16c69eb7\"],\"snapshot_id\":\"3ff31378-a8bf-4f80-ab5b-659c42a8cc75\"}"
```

Playbook name which uses the abovementioned module: create_server.yaml
The playbook (due to its integration with DNSimple) will request API email address, token and domain name to use for the A DNS record creation.

Usage:
```bash
ansible-playbook create_server.yaml -e name=_new-servername
```

Where the directory name, configuration and python script all share the same name, in this case: `vultr`.

The configuration file is fairly simple. Split in two halves, one for the inventory and another for the module runtime. The module object consists of multiple endpoints, each of which can have various options, it is really up to the one who creates the python script to manage the data there.
```yaml
---
#vultr.yaml
apitoken: "API_TOKEN_HERE"

inventory:
  endpoint: "https://api.vultr.com/v2/instances"
  options:
    method: "GET"
    headers:
      - authorization: "Bearer {{ apitoken }}"
      - content-type: "application/json"

module:
  create:
    endpoint: "https://api.vultr.com/v2/instances"
    options:
      method: "POST"
  get:
    endpoint: ".../"
  options:
    endpoint: "..../"
```

The python script should define the following two methods:

`collect()` which is utilized by the inventory plugin
`mod()` which is used by the python module to run specific commands

This design decision was made to support any number of upstream providers, while the inventory plugin remains unified.
