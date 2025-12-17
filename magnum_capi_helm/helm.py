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

import datetime
import functools
import json
import pathlib
import requests
import time
import typing as t

from magnum.common import utils
from oslo_concurrency import processutils
from oslo_log import log as logging

from magnum_capi_helm import conf
from magnum_capi_helm import kubernetes

LOG = logging.getLogger(__name__)
CONF = conf.CONF

# This code is loosely based on:
#  https://github.com/azimuth-cloud/pyhelm3
#  Ideally we can share this code in the future.


def mergeconcat(defaults, *overrides):
    """Deep-merge two or more dictionaries together.

    Lists are concatenated.
    """

    def mergeconcat2(defaults, overrides):
        if isinstance(defaults, dict) and isinstance(overrides, dict):
            merged = dict(defaults)
            for key, value in overrides.items():
                if key in defaults:
                    merged[key] = mergeconcat2(defaults[key], value)
                else:
                    merged[key] = value
            return merged
        elif isinstance(defaults, (list, tuple)) and isinstance(
            overrides, (list, tuple)
        ):
            merged = list(defaults)
            merged.extend(overrides)
            return merged
        else:
            return overrides if overrides is not None else defaults

    return functools.reduce(mergeconcat2, overrides, defaults)


class Client:
    """Client for interacting with Helm CLI."""

    def __init__(self):
        self._default_timeout = "5m"
        self._executable = "helm"
        self._history_max_revisions = 10
        self._kubeconfig = CONF.capi_helm.kubeconfig_file

    def _run(self, command, **kwargs) -> bytes:
        command = [self._executable] + command
        if self._kubeconfig:
            command.extend(["--kubeconfig", self._kubeconfig])
        stdout, stderr = utils.execute(*command, **kwargs)
        LOG.debug(f"Ran helm {command} got out:{stdout} err:{stderr}")
        return stdout

    def install_or_upgrade(
        self,
        release_name: str,
        chart_ref: t.Union[pathlib.Path, str],
        *values: t.Dict[str, t.Any],
        namespace: str,
        repo: t.Optional[str] = None,
        version: t.Optional[str] = None,
    ) -> t.Iterable[t.Dict[str, t.Any]]:
        """Install or upgrade specified release using chart and values."""
        assert release_name is not None
        command = [
            "upgrade",
            release_name,
            chart_ref,
            "--history-max",
            self._history_max_revisions,
            "--install",
            "--output",
            "json",
            "--timeout",
            self._default_timeout,
            # We send the values in on stdin
            "--values",
            "-",
            "--namespace",
            namespace,
        ]
        if repo:
            command += ["--repo", repo]
        if version:
            command += [
                "--version",
                version,
            ]

        process_input = json.dumps(mergeconcat({}, *values))
        return json.loads(self._run(command, process_input=process_input))

    def uninstall_release(
        self,
        release_name: str,
        namespace: str,
    ):
        """Uninstall the named release."""
        assert release_name is not None
        command = [
            "uninstall",
            release_name,
            "--timeout",
            self._default_timeout,
            "--namespace",
            namespace,
        ]
        try:
            self._run(command)
        except processutils.ProcessExecutionError as exc:
            # Swallow release not found errors, as that is our desired state
            if not exc.stderr or "release: not found" not in exc.stderr:
                raise


class HelmLockException(Exception):
    pass


class HelmLock:
    """Context manager to provide locking semantics for Helm commands.

    Uses the Kubernetes leases.coordination.k8s.io/v1 API.
    """

    def __init__(
        self, release_name: str, namespace: str, timeout_seconds: int = 300
    ):
        self._lease_duration_seconds = 300
        self._wait_timeout_seconds = timeout_seconds
        self._k8s_client = kubernetes.Client.load()
        self.namespace = namespace
        self.release_name = release_name
        self.lease_name = f"capi-helm-{release_name}"

    def __enter__(self):
        for i in range(self._wait_timeout_seconds):
            if self._acquire_lock():
                return
            LOG.debug(
                "Waiting for lock on Helm release "
                f"{self.namespace}/{self.release_name}"
            )
            time.sleep(1)
        raise HelmLockException(
            f"Timed out waiting {self._wait_timeout_seconds} for Helm lock"
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._k8s_client.delete_lease(self.release_name, self.namespace)

    def _acquire_lock(self) -> bool:
        """Attempts to acquire a lease for the given Helm release.

        Returns True when lease is successfully acquired or False otherwise.
        The caller is responsible for retrying acquisition if False.
        """

        lease = self._k8s_client.get_lease(self.lease_name, self.namespace)
        LOG.debug(
            f"Lease for Helm release {self.namespace}/{self.release_name}: "
            f"{lease}"
        )

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        lease_data = {
            "metadata": {"resourceVersion": None},
            "spec": {
                "acquireTime": now_str,
                "renewTime": now_str,
                "holderIdentity": "TODO",
                "leaseDurationSeconds": self._lease_duration_seconds,
            },
        }

        # If lease doesn't exist, we're free to create one and acquire the lock
        if lease is None:
            LOG.debug(
                "Creating new lease for Helm release "
                f"{self.namespace}/{self.release_name}"
            )
            self._k8s_client.apply_lease(
                self.lease_name, lease_data, self.namespace
            )
            return True

        # If lease exists, we need to use the existing resourceVersion
        # to allow k8s to coordinate lease updates correctly
        if lease.get("metadata", {}).get("resourceVersion"):
            lease_data["metadata"] = {
                "resourceVersion": lease["metadata"]["resourceVersion"]
            }

        renew_time = lease.get("spec", {}).get("renewTime")
        if renew_time is None:
            raise HelmLockException("renewTime should not be None")
        print("Renew time:", renew_time)
        renew_time = datetime.datetime.fromisoformat(
            renew_time.replace("Z", "+00:00")
        )

        ttl = lease.get("spec", {}).get("leaseDurationSeconds")
        if ttl is None:
            raise HelmLockException("leaseDurationSections should not be None")
        lease_duration = datetime.timedelta(seconds=ttl)

        # If the lease has expired then previous holder must have failed
        # to delete it when finished so we can acquire it anyway
        if renew_time + lease_duration < now:
            LOG.debug(
                "Found expired lease for Helm release "
                f"{self.namespace}/{self.release_name}"
            )
            try:
                self._k8s_client.apply_lease(
                    self.lease_name, lease_data, self.namespace
                )
            except requests.exceptions.HTTPError as exc:
                # If we try to apply a lease with an older version
                # (e.g. because another conductor updated the lease
                # after we fetched it) k8s will return an HTTP 409 response.
                # This is equivalent to failing to acquire the lock.
                if exc.response.status_code == 409:
                    return False
                raise exc
            return True

        return False
