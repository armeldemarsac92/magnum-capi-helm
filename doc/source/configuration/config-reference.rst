=======================
Configuration reference
=======================

All configuration options listed bellow are used in
[capi_helm] stanza in magnum.conf file.

**kubeconfig_file**

    **default**: none

    **type**: string

     Path to a kubeconfig file for a management cluster,
     for use in the Cluster API driver.
     Defaults to the environment variable KUBECONFIG,
     or if not defined ~/.kube/config

**namespace_prefix**

    **type**: string

    **default**: magnum

     Resources for each openstack cluster are created in a
     separate namespace within the CAPI Management cluster
     specified by the configuration: [capi_helm]/kubeconfig_file
     You should modify this prefix when two magnum deployments
     want to share a single CAPI management cluster.

**helm_chart_repo**

    **type**: string

    **default**: https://azimuth-cloud.github.io/capi-helm-charts

     Reference to the helm chart repository for
     the CAPI Helm driver.
     Note that if helm_chart_name starts with oci://
     this must be empty string.

     Related options:
        * helm_chart_name
        * default_helm_chart_version


**helm_chart_name**

    **type**: string

    **default**: openstack-cluster

     Name of the helm chart to use from the repo specified
     by the config: capi_driver.helm_chart_repo

     Related options:
      * helm_chart_repo
      * default_helm_chart_version


**default_helm_chart_version**

    **type**: string

    **default**: 0.10.1

     Version of the helm chart specified
     by the config: capi_driver.helm_chart_repo
     and capi_driver.helm_chart_name.
     A cluster label can override this.

     Related options:
     * helm_chart_name
     * helm_chart_repo

**helm_value_override_files**

    **type**: string

    **default**: none

    A comma separated key:value list where the key corresponds
    to the label 'helm_value_override_files' on cluster templates
    and the key 'all' is applied to all clusters.
    The value must be a path to file of a yaml values file that is
    used as overrides to the helm chart.
    This can be useful to apply operator customisations to helm
    charts without modifying and publishing the entire chart.
    Take care to not break existing clusters that may already
    be using the configured labels.


**minimum_flavor_ram**

    **type**: integer

    **default**: 2048

    Minimum RAM (in MB units) for flavor used to create a Kubernetes node.


**minimum_flavor_vcpus**

    **type**: integer

    **default**: 2

    Minimum VCPUS for flavor used to create a Kubernetes node.


**csi_cinder_default_volume_type**

    **type**: string

    **Default**: Cinder volume type for default StorageClass.


**csi_cinder_reclaim_policy**

    **type**: string

    **default**: Retain

     Policy for reclaiming dynamically created
     persistent volumes. Can be 'Retain' or 'Delete'.


**csi_cinder_allow_volume_expansion**

    **type**: bool

    **default**: True

     Allows the users to resize the volume by
     editing the corresponding PVC object.

**csi_cinder_allowed_topologies**

    **default**: []

     Select the Nodes where the application
     Pods may be scheduled based on Node labels.


**csi_cinder_fstype**

    **type**: string

    **default**: ext4

    Filesystem type for persistent volumes.


**csi_cinder_volume_binding_mode**

    **type**: string

    **default**: Immediate

     The volumeBindingMode field controls when
     volume binding and dynamic provisioning should occur.


**csi_cinder_availability_zone**

    **type**: string

    **default**: nova

    The default availability zone to use for Cinder volumes.


**app_cred_interface_type**

    **type**: string

    **default**: public

     The value to use in the interface field of
     generated application credentials.


**api_resources**

    **type**: string

    **default**: {}

    Dictionary of cluster api resources to modify
    api_version and plural names in string format.
    Example::

      '{
          K8sControlPlane: {
              api_version: controlplane.cluster.x-k8s.io/v1beta1,
              plural_name: kubeadmcontrolplanes
          },
          OpenstackCluster: {
              api_version: infrastructure.cluster.x-k8s.io/v1beta1,
          },
      }'


**k8s_control_plane_resource_conditions**

    **type**: list

    **default**::

      [
        MachinesReady,
        Ready,
        EtcdClusterHealthy,
        ControlPlaneComponentsHealthy,
      ]


    List of conditions to check for kubernetes control plane
    resource to consider as ready.
