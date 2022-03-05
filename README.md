A showcase Ansible playbook and inventory plugin, which gathers instances data from remote provider and creates A records for each instance.

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

Where the directory name, configuration and python script all share the same name, in this case: `vultr`.

The configuration file is fairly simple, we need an endpoint link, method and some headers:
```yaml
---
#vultr.yaml

endpoint: "https://api.vultr.com/v2/instances"
options:
  method: "GET"
  headers:
    - authorization: "Bearer UPSTREAM_API_TOKEN_HERE"
    - content-type: "application/json"
```

The python script file should define a `collect(config=Object)` method, which returns list of servers in a specific format.

This design decision was made to support any number of upstream providers, while the inventory plugin remains unified.
