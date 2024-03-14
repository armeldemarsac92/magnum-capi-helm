..
      Copyright 2014-2015 OpenStack Foundation
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

===================================================
Welcome to Magnum CAPI Helm Driver's documentation!
===================================================

OpenStack Magnum driver using helm to create k8s clusters with Cluster API.

The driver uses capi-helm-charts to create the k8s resources needed to create a
k8s cluster using Cluster API, including various useful add ons like a CNI and
a monitoring stack.

Note, the helm charts are intended to be a way to share a reference method to
create K8s on OpenStack. The charts are not expected or intended to be specific
to Magnum. The hope is they can also be used by ArgoCD, Flux or Azimuth to
create k8s clusters on OpenStack.

* **Free software:** under the `Apache license <http://www.apache.org/licenses/LICENSE-2.0>`_
* **Source:** https://opendev.org/openstack/magnum-capi-helm
* **Blueprints:** https://blueprints.launchpad.net/magnum
* **Bugs: (use magnum-capi-helm tag)** https://bugs.launchpad.net/magnum
* **Magnum Source:** https://opendev.org/openstack/magnum
* **Magnum REST Client:** https://opendev.org/openstack/python-magnumclient

Installation Guide
------------------

.. toctree::
   :maxdepth: 2

   Installation Guide <install/index>

Configuration Reference
-----------------------
.. toctree::
   :maxdepth: 2

   configuration/index

Contributor Guide
-----------------

.. toctree::
   :maxdepth: 2

   contributor/index

