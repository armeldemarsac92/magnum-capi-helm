===================
Configuration Guide
===================

For complete reference of configuration options for this driver used in
magnum.conf plesese refer to:

.. toctree::
   :maxdepth: 1

   Configuration Reference <config-reference>

Features
========

The driver currently supports create, delete and upgrade operations as well
as updates to node groups and their sizes.

The Kubernetes versions against which the CAPI Helm charts are currently being
tested can be found `here <https://github.com/azimuth-cloud/capi-helm-charts/blob/main/.github/workflows/ensure-capi-images.yaml#L9>`__.

The driver respects the following cluster and template properties:

* image_id
* keypair
* fixed_network, fixed_subnet (if missing, a new one is created
  with CIDR: 10.0.0.0/24)
* external_network_id
* dns_nameserver

The driver supports the following labels:



+-----------------------------------+---------------------+
| Label                             | Default             |
+===================================+=====================+
| monitoring_enabled                | false               |
|                                   |                     |
+-----------------------------------+---------------------+
| kube_dashboard_enabled            | true                |
|                                   |                     |
+-----------------------------------+---------------------+
| octavia_provider                  | amphora             |
|                                   |                     |
+-----------------------------------+---------------------+
| fixed_subnet_cidr                 | 10.0.0.0/24         |
+-----------------------------------+---------------------+
| extra_network_name                | empty               |
+-----------------------------------+---------------------+
| capi_helm_chart_version           | 0.10.1              |
| (see bellow for additional info)  |                     |
+-----------------------------------+---------------------+
| helm_extra_values                 | ""                  |
| (see bellow for additional info)  |                     |
+-----------------------------------+---------------------+
| etcd_blockdevice_size             | 0                   |
+-----------------------------------+---------------------+
| etcd_volume_size                  | 0                   |
+-----------------------------------+---------------------+
| etcd_blockdevice_type             | volume              |
|                                   |                     |
+-----------------------------------+---------------------+
| etcd_blockdevice_volume_az        | ""                  |
+-----------------------------------+---------------------+
| csi_cinder_availability_zone      | ""                  |
+-----------------------------------+---------------------+
| csi_cinder_reclaim_policy         | Delete              |
|                                   |                     |
+-----------------------------------+---------------------+
| csi_cinder_fstype                 | ext4                |
+-----------------------------------+---------------------+
| csi_cinder_allow_volume_expansion | True                |
|                                   |                     |
+-----------------------------------+---------------------+
| octavia_provider                  | amphora             |
|                                   | ovn                 |
+-----------------------------------+---------------------+
| octavia_lb_algorithm              | ROUND_ROBIN,        |
|                                   | SOURCE_IP_PORT if   |
|                                   | octavia_provider is |
|                                   | set to "ovn".       |
+-----------------------------------+---------------------+
| boot_volume_type                  | nvme                |
+-----------------------------------+---------------------+
| extra_network_name                | ""                  |
|                                   |                     |
+-----------------------------------+---------------------+



Two config options require a little bit more explanation:


* capi_helm_chart_version: can only be set via template property
  and CAN'T be overridden by cli options. If not set in cluster template,
  value is taken from magnum.config option default_helm_chart_version.


* helm_extra_values: Allows operators to map arbitrary cluster
  template labels to snippets of Helm value overrides. See example
  below for more details.
  As an operator, you **must** be careful to not make changes
  to existing clusters that are not backwards compatible.
  And you must not remove any configuration that applies to
  existing templates, unless that is backwards compatible. Following
  examples are presenting usage of this functionality


Examples
========

**Exapmle #1** Using "all" clause to override cidrBlocks for pods and services


.. note::

  In this example one don't need to add label to cluster template to point
  magnum to right file with helm values override. **all**  clause is
  applied to ALL clusters.



We want to override CIDR block used by all k8s clusters spawned
because default ones are conflicting with underlying infrastracure and
clusters don't spawn correctly. Additonally we want to change IP pool for
services.

CIDR blocks definitions responsible for this are defined in helm chart `here <https://github.com/azimuth-cloud/capi-helm-charts/blob/f0ce6fda1cc5b836bd8d9f9235771234be4af9e4/charts/openstack-cluster/values.yaml#L61>`__.

We can achive our gole by overrriding those values. In order to do this we will
use "all" clause described above.

We have cluster template without label and value for helm_extra_values.

In /etc/magnum/magnum.conf we ned to add:::

  [capi_helm]
  helm_value_override_files = all:/etc/magnum/all.yml

And content of /etc/magnum/all.conf:::

    kubeNetwork:
      pods:
        cidrBlocks:
          - 192.168.2.0/24
      services:
        cidrBlocks:
          - 172.24.4.0/13

After spawning cluster you will notice that pods (apart of pods that need have
access to underlying host network) will have IP from 192.168.2.0/24 pool,
and services will have IP from 172.24.4.0/13:

::

   ubuntu@magnum-devstack:~$ kubectl get pods -A -o wide
   NAMESPACE         NAME                                      READY  STATUS   IP
   calico-apiserver  calico-apiserver-545c94bd7b-7mz9z         1/1    Running  192.168.2.133
   calico-apiserver  calico-apiserver-545c94bd7b-xt86l         1/1    Running  192.168.2.4
   calico-system     calico-kube-controllers-5f7f9fdbc5-szfsd  1/1    Running  192.168.2.130
   calico-system     calico-node-695jb                         1/1    Running  10.0.0.135
   calico-system     calico-node-6pjgd                         1/1    Running  10.0.0.127

::

   ubuntu@magnum-devstack:~$ kubectl get svc -A
   NAMESPACE          NAME                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                  AGE
   calico-apiserver   calico-api                        ClusterIP   172.29.28.225    <none>        443/TCP                  82m
   calico-system      calico-kube-controllers-metrics   ClusterIP   None             <none>        9094/TCP                 80m
   calico-system      calico-typha                      ClusterIP   172.30.122.228   <none>        5473/TCP                 82m
   calico-system      calico-typha-metrics              ClusterIP   172.24.189.140   <none>        9093/TCP                 82m
   default            kubernetes                        ClusterIP   172.24.0.1       <none>        443/TCP                  83m
   gpu-operator       gpu-operator                      ClusterIP   172.30.128.171   <none>        8080/TCP                 79m
   gpu-operator       nvidia-dcgm-exporter              ClusterIP   172.27.220.18    <none>        9400/TCP                 79m
   gpu-operator       nvidia-node-status-exporter       ClusterIP   172.31.110.109   <none>        8000/TCP                 79m
   kube-system        kube-dns                          ClusterIP   172.24.0.10      <none>        53/UDP,53/TCP,9153/TCP   83m
   kube-system        metrics-server                    ClusterIP   172.27.138.61    <none>        443/TCP                  82m




**Exapmle #2** Using labels to override cidrBlocks for pods and services
for cluster.

This example is similar to previous one, with exception that we need
to point which clusters will be altered.
Like in previous example CIDR blocks definitions responsible for this are
defined in helm chart
`here <https://github.com/azimuth-cloud/capi-helm-charts/blob/f0ce6fda1cc5b836bd8d9f9235771234be4af9e4/charts/openstack-cluster/values.yaml#L61>`__.

To override them only in part of our clusters we
need to have cluster template with label and value helm_extra_values = 'cidr'

This should point to key which maps to file with values for chart,
in variable helm_value_override_files in magnum.conf::

  [capi_helm]
  helm_value_override_files = cidr:/etc/magnum/cidr.yml

In /etc/magnum/magnum.conf we need to add:::

  [capi_helm]
  helm_value_override_files = cidr:/etc/magnum/all.yml

And content of /etc/magnum/cidr.conf:::

    kubeNetwork:
      pods:
        cidrBlocks:
          - 192.168.2.0/24
      services:
        cidrBlocks:
          - 172.24.4.0/13

After spawning cluster you will notice that pods (apart of pods that need have
access to underlying host network) will have IP from 192.168.2.0/24 pool,
and services will have IP from 172.24.4.0/13 (few columns are ommited
for readybility):

::

   ubuntu@magnum-devstack:~$ kubectl get pods -A -o wide
   NAMESPACE         NAME                                      READY  STATUS   IP
   calico-apiserver  calico-apiserver-5d6bd49c6d-2dzf4         1/1    Running  192.168.2.197
   calico-apiserver  calico-apiserver-5d6bd49c6d-jqwnf         1/1    Running  192.168.2.204
   calico-system     calico-kube-controllers-994ddbfb6-vhqsh   1/1    Running  192.168.2.203
   calico-system     calico-node-5fzxh                         1/1    Running  10.0.0.171
   calico-system     calico-node-7sg4c                         1/1    Running  10.0.0.73
   calico-system     calico-node-fp478                         1/1    Running  10.0.0.158

::

   ubuntu@magnum-devstack:~$ kubectl get svc -A
   NAMESPACE          NAME                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)
   calico-apiserver   calico-api                        ClusterIP   172.31.47.224    <none>        443/TCP
   calico-system      calico-kube-controllers-metrics   ClusterIP   None             <none>        9094/TCP
   calico-system      calico-typha                      ClusterIP   172.24.55.50     <none>        5473/TCP
   calico-system      calico-typha-metrics              ClusterIP   172.24.172.63    <none>        9093/TCP
   default            kubernetes                        ClusterIP   172.24.0.1       <none>        443/TCP
   gpu-operator       gpu-operator                      ClusterIP   172.25.248.47    <none>        8080/TCP
   gpu-operator       nvidia-dcgm-exporter              ClusterIP   172.31.40.179    <none>        9400/TCP
   gpu-operator       nvidia-node-status-exporter       ClusterIP   172.26.20.61     <none>        8000/TCP
   kube-system        kube-dns                          ClusterIP   172.24.0.10      <none>        53/UDP,53/TCP,9153/TCP
   kube-system        metrics-server                    ClusterIP   172.28.122.132   <none>        443/TCP


In similar fashion all values from linked charts can ben ovewriten and even
expanded by aditional charts. Which leads us to...



**Exapmle** #3 Ading custom chart to the mix

We have cluster template with label and value helm_extra_values = 'zabbix'

This should point to key which maps to file with values for chart,
in variable helm_value_override_files in magnum.conf::

  [capi_helm]
  helm_value_override_files = zabbix:/etc/magnum/zabbix.yml


Content of /etc/magnum/zabbix.yml file should look like this:::


    addons:
      custom:
        zabbix-helm-release:
          kind: HelmRelease
          spec:
            namespace: zabbix
            chart:
              repo: https://cdn.zabbix.com/zabbix/integrations/kubernetes-helm/7.4
              name: zabbix-helm-chart
              version: 1.6.8
            values:
              zabbixProxy:
                env:
                  - name: ZBX_SERVER_HOST
                    value: "172.16.1.114"
                  - name: ZBX_HOSTNAME
                    value: "zabbix-proxy"
                image:
                  tag: alpine-7.4-latest


After spawning cluster your zabbix deployment will be there:

::

  ubuntu@magnum-devstack:~$ kubectl get pods -n zabbix -o wide
  NAME                                                           READY   STATUS    RESTARTS   AGE     IP
  zabbix-helm-release-kube-state-metrics-849523f5bd-rr7b3        1/1     Running   0          5m      10.0.0.129
  zabbix-helm-release-zabbix-helm-chart-agent-29dq8              1/1     Running   0          3m16s   10.0.0.240
  zabbix-helm-release-zabbix-helm-chart-agent-29g64              1/1     Running   0          3m32s   10.0.0.91
  zabbix-helm-release-zabbix-helm-chart-agent-lpqzm              1/1     Running   0          3m9s    10.0.0.72
  zabbix-helm-release-zabbix-helm-chart-proxy-759589cb9b-ck837   1/1     Running   0          5m      10.10.0.13


::

  ubuntu@magnum-devstack:~$ kubectl get svc -n zabbix -o wide
  NAME                                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)
  zabbix-helm-release-kube-state-metrics        ClusterIP   172.30.135.174   <none>        8080/TCP
  zabbix-helm-release-zabbix-helm-chart-agent   ClusterIP   172.24.156.131   <none>        10050/TCP
  zabbix-helm-release-zabbix-helm-chart-proxy   ClusterIP   172.27.149.48   <none>        10051/TCP


**Example #4** Putting it all together.

Lets combine our exapmles #1 and #3 above into one!

We need our cidr blocks changed for all clusters, but we need install zabbix
just into one extremly importat cluster for constant monitoring.

In that case magnum.conf should contain::

  [capi_helm]
  helm_value_override_files = zabbix:/etc/magnum/zabbix.yml,all:/etc/magnum/all.yml

Content of /etc/magnum/zabbix.yml file should look like this::


    addons:
      custom:
        zabbix-helm-release:
          kind: HelmRelease
          spec:
            namespace: zabbix
            chart:
              repo: https://cdn.zabbix.com/zabbix/integrations/kubernetes-helm/7.4
              name: zabbix-helm-chart
              version: 1.6.8
            values:
              zabbixProxy:
                env:
                  - name: ZBX_SERVER_HOST
                    value: "172.16.1.114"
                  - name: ZBX_HOSTNAME
                    value: "zabbix-proxy"
                image:
                  tag: alpine-7.4-latest


And content of /etc/magnum/cidr.conf:::

    kubeNetwork:
      pods:
        cidrBlocks:
          - 192.168.2.0/24
      services:
        cidrBlocks:
          - 172.24.4.0/13



As a result, after spawning cluster, we will have Zabbix agent deployed with ip
addresses from pool defined by us.


::

  ubuntu@magnum-devstack:~$ kubectl get pods -n zabbix -o wide
  NAME                                                           READY   STATUS    RESTARTS   AGE     IP
  zabbix-helm-release-kube-state-metrics-849595f5bd-r7rl4        1/1     Running   0          5m      192.168.2.129
  zabbix-helm-release-zabbix-helm-chart-agent-29dq8              1/1     Running   0          3m16s   10.0.0.240
  zabbix-helm-release-zabbix-helm-chart-agent-29g64              1/1     Running   0          3m32s   10.0.0.91
  zabbix-helm-release-zabbix-helm-chart-agent-lpqzm              1/1     Running   0          3m9s    10.0.0.72
  zabbix-helm-release-zabbix-helm-chart-proxy-759576cb9b-cl847   1/1     Running   0          5m      192.168.2.130


::

  ubuntu@magnum-devstack:~$ kubectl get svc -n zabbix -o wide
  NAME                                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)
  zabbix-helm-release-kube-state-metrics        ClusterIP   172.30.149.174   <none>        8080/TCP
  zabbix-helm-release-zabbix-helm-chart-agent   ClusterIP   172.24.142.131   <none>        10050/TCP
  zabbix-helm-release-zabbix-helm-chart-proxy   ClusterIP   172.27.127.148   <none>        10051/TCP

Tip & Tricks
=============

Currently, all clusters use the Calico CNI. While Cilium is also supported
in the Helm charts, it is not currently regularly tested.

We have found that cluster upgrades with ClusterAPI don't work well without
using a load balancer, even with a single node control plane, so we currently
ignore the "master-lb-enabled" flag.


