# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Collection of static functions that are shared within the driver.

import re

from magnum_capi_helm import conf

CONF = conf.CONF


def cluster_namespace(cluster):
    # We create clusters in a project-specific namespace
    # To generate the namespace, first sanitize the project id
    project_id = re.sub("[^a-z0-9]", "", cluster.project_id.lower())
    prefix = CONF.capi_helm.namespace_prefix
    return f"{prefix}-{project_id}"


def sanitized_name(name, suffix=None):
    if not name:
        return None
    return re.sub(
        "[^a-z0-9]+",
        "-",
        (f"{name}-{suffix}" if suffix else name).lower(),
    ).strip("-")


RELEASE_NAME_LABEL = "magnum_capi_helm_release"


def chart_release_name(cluster):
    return (cluster.labels or {}).get(RELEASE_NAME_LABEL)


def migrate_release_name(cluster):
    """Copy stack_id -> label for Magnum 2026.2 (Hibiscus) compatibility.

    stack_id was dropped from the Cluster object in that release.  Safe to
    call after the field is gone: getattr returns None silently.
    """
    if chart_release_name(cluster):
        return
    stack_id = getattr(cluster, "stack_id", None)
    if stack_id:
        if cluster.labels is None:
            cluster.labels = {}
        cluster.labels[RELEASE_NAME_LABEL] = stack_id
        cluster.save()


def get_k8s_resource_name(cluster, name):
    return sanitized_name(chart_release_name(cluster), name)
