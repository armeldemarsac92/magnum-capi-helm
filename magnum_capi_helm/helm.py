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

import functools
import json
import pathlib
import typing as t

from magnum.common import utils
from oslo_concurrency import processutils
from oslo_log import log as logging

from magnum_capi_helm import conf

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

        try:
            process_output = self._run(command, process_input=process_input)
            result = json.loads(process_output)
        except processutils.ProcessExecutionError as exc:
            # If other updates are being applied concurrently, we can get:
            # another operation (install/upgrade/rollback) is in progress
            if (
                exc.stderr
                and (
                    "another operation (install/upgrade/rollback) is in "
                    "progress" in exc.stderr
                )
                or ("release: already exists" in exc.stderr)
            ):
                LOG.info(
                    f"Helm update conflict for {release_name}, retry required"
                )
            else:
                LOG.info(
                    f"Helm upgrade failed for {release_name}, "
                    f"unknown reason: {exc}"
                )
            # Retry reconciliation on a later attempt
            return {}
        return result

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

    def update_pending(
        self,
        release_name: str,
        chart_version: str,
        chart_name: str,
        cluster_values: t.Dict[str, t.Any],
        namespace: str,
    ):
        """Check for difference between cluster state and Helm state.

        Returns True if changes need to be applied, False otherwise.

        :param release_name: Cluster unique name, as used for instance prefix
        :param chart_version: Helm chart version
        :param chart_name: Helm chart name
        :param cluster_values: Values for Helm chart
        :param namespace: Cluster kubernetes namespace
        """

        cmd_meta = [
            "get",
            "metadata",
            "--namespace",
            namespace,
            release_name,
            "--output",
            "json",
        ]
        try:
            output_meta = self._run(cmd_meta)
            chart_meta = json.loads(output_meta)
        except processutils.ProcessExecutionError as exc:
            # Swallow release not found errors - all change in that case
            if not exc.stderr or "release: not found" not in exc.stderr:
                raise
            return True

        if (
            "revision" not in chart_meta
            or "chart" not in chart_meta
            or "status" not in chart_meta
            or "version" not in chart_meta
        ):
            LOG.debug(
                f"{release_name}: incomplete chart metadata: update needed"
            )
            return True

        if chart_meta["chart"] != chart_name:
            LOG.debug(
                f"{release_name}: chart name update "
                f"{chart_meta['chart']}->{chart_name}: "
                f"update needed"
            )
            return True

        if chart_meta["status"] != "deployed":
            LOG.debug(
                f"{release_name}: release status "
                f"{chart_meta['status']}: update needed"
            )
            return True

        if chart_meta["version"] != chart_version:
            LOG.debug(
                f"{release_name}: chart version update "
                f"{chart_meta['version']}->{chart_version}: "
                f"update needed"
            )
            return True

        # Further details needed: compare release values
        cmd_values = [
            "get",
            "values",
            "--namespace",
            namespace,
            release_name,
            "--output",
            "json",
        ]
        try:
            output_values = self._run(cmd_values)
            chart_values = json.loads(output_values)
        except processutils.ProcessExecutionError as exc:
            # Cluster has disappeared since the last helm exec?
            # Swallow release not found errors - all change in that case
            if not exc.stderr or "release: not found" not in exc.stderr:
                raise
            return True

        if chart_values != cluster_values:
            LOG.debug(f"{release_name}: change in chart values: update needed")
            return True

        # No updates to apply to release state
        LOG.debug(f"{release_name}: no update needed")
        return False
