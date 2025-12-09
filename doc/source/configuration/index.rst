===================
Configuration Guide
===================

Features
========

The driver currently supports create, delete and upgrade operations as well
as updates to node groups and their sizes.

The Kubernetes versions against which the CAPI Helm charts are currently being tested
can be found `here <https://github.com/azimuth-cloud/capi-helm-charts/blob/main/.github/workflows/ensure-capi-images.yaml#L9>`_.

The driver respects the following cluster and template properties:

* image_id
* keypair
* fixed_network, fixed_subnet (if missing, a new one is created
  with CIDR: 10.0.0.0/24)
* external_network_id
* dns_nameserver

The driver supports the following labels:


+-------------------------+-------------+-----------------+
| Label                   | Default     | Possible values |
+=========================+=============+=================+
| monitoring_enabled      | false       | false           |
|                         |             |  true           |
+-------------------------+-------------+-----------------+
| kube_dashboard_enabled  | true        |  true           |
|                         |             |  false          |
+-------------------------+-------------+-----------------+
| octavia_provider        | amphora     |  amphora        |
|                         |             |  ovn            |
+-------------------------+-------------+-----------------+
| fixed_subnet_cidr       | 10.0.0.0/24 | CIDR            |
+-------------------------+-------------+-----------------+
| extra_network_name      | empty       | CIDR            |
+-------------------------+-------------+-----------------+
| capi_helm_chart_version | 0.10.1      | existing chart  |
|                         |             | version         |
+-------------------------+-------------+-----------------+
| helm_extra_values       | filepath    | accessible file |
+-------------------------+-------------+-----------------+


**TODO: Add more recently supported labels here.**


* capi_helm_chart_version: can only be set via template property
  and CAN'T be overrided by cli options. If not set in cluster template,
  value is taken from magnum.config option default_helm_chart_version.
  If not found there it defaults to 0.10.1

* helm_extra_values: used to point key in dictionary
  mapping file with value ovverrides for clusters with this label.

Example:

We have cluster template with label and value: helm_extra_values 'zabbix'

This should point to key which maps to file with values for chart,
in variable helm_value_override_files in magnum.conf::

  [capi_helm]
  helm_value_override_files = zabbix:/etc/magnum/zabbix.yml


Content of /etc/magnum/zabbix.yml file should look like this:



    root@magnum-devstack:/etc/magnum# cat /etc/magnum/zabbix.yml

    addons:
      custom:
        zabbix-helm-release:
          spec:
            values:
              zabbixProxy:
                env:
                  - name: ZBX_SERVER_HOST
                    value: "<your_zabbix_proxy_ip>"
                  - name: ZBX_HOSTNAME
                    value: "your_zabbix_proxy"
                image:
                  tag: alpine-7.4-latest




Currently, all clusters use the Calico CNI. While Cilium is also supported
in the Helm charts, it is not currently regularly tested.

We have found that cluster upgrades with ClusterAPI don't work well without
using a load balancer, even with a single node control plane, so we currently
ignore the "master-lb-enabled" flag.
