===============================
magnum-capi-helm
===============================

OpenStack Magnum driver using Helm to create k8s clusters
with Cluster API.

The driver uses `capi-helm-charts <https://github.com/azimuth-cloud/capi-helm-charts>`_
to create the k8s resources needed to provision a k8s cluster using
Cluster API, including various useful add-ons like a CNI and a monitoring
stack.


Note, the above Helm charts are intended to be
a way to share a reference method to create K8s
on OpenStack. The charts are not expected or
intended to be specific to Magnum. The hope is
they can also be used by ArgoCD, Flux or Azimuth
to create k8s clusters on OpenStack.


Compatible versions
===================

Due to the fast-changing nature of Cluster API and Cluster API OpenStack provider <https://github.com/kubernetes-sigs/cluster-api-provider-openstack>_, care should be taken to keep 


.. list-table:: Versions
   :header-rows: 1

   * - magnum-capi-helm (Driver)
     - capi-helm-chart (Helm Chart)
     - cluster-api-provider-openstack (Cluster-API OpenStack provider)
   * - Row 1, column 1
     -
     - Row 1, column 3
   * - Row 2, column 1
     - Row 2, column 2
     - Row 2, column 3

https://github.com/kubernetes-sigs/cluster-api-provider-openstack

History
=======

Work on this driver started upstream around October 2021.
After failing to get merged during Bobcat,
we created this downstream repo as a stop-gap to help
those wanting to use this driver now.
https://specs.openstack.org/openstack/magnum-specs/specs/bobcat/clusterapi-driver.html
