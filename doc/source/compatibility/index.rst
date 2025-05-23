======================
Compatiblity Reference
======================

Due to the fast-changing nature of Cluster API and Cluster API OpenStack
provider, care should be taken to keep the different versions compatible.

There are 3 parts needs to be keep compatible.

* **magnum-capi-helm**: This driver
* **capi-helm-chart**: Helm Chart <https://github.com/azimuth-cloud/capi-helm-charts>_
* **cluster-api-provider-openstack**: Cluster API OpenStack provider -
  <https://github.com/kubernetes-sigs/cluster-api-provider-openstack>_


.. list-table:: Versions
   :header-rows: 1

   * - magnum-capi-helm
     - capi-helm-chart
     - cluster-api-provider-openstack
   * - 1.2.1
     - >= 0.1.3
     - >=0.8.0
