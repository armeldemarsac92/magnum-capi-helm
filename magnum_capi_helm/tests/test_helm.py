#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime
from unittest import mock

import requests
import yaml

from magnum.common import utils
from oslo_concurrency import processutils

from magnum_capi_helm import helm
from magnum_capi_helm import kubernetes
from magnum_capi_helm.tests import base


class TestHelmClient(base.TestCase):
    def test_mergeconcat_dicts(self):
        defaults = dict(foo="bar", asdf=dict(a="b", c="d"))
        overrides = dict(asdf=dict(a="c"))

        result = helm.mergeconcat(defaults, overrides)

        expected = dict(foo="bar", asdf=dict(a="c", c="d"))
        self.assertEqual(expected, result)

    def test_mergeconcat_list(self):
        defaults = ["foo", "bar"]
        overrides = ["bar", "baz"]

        result = helm.mergeconcat(defaults, overrides)

        expected = ["foo", "bar", "bar", "baz"]
        self.assertEqual(expected, result)

    @mock.patch.object(utils, "execute")
    def test_install_or_upgrade(self, mock_execute):
        mock_execute.return_value = '[{"foo": "bar"}]', ""

        client = helm.Client()
        result = client.install_or_upgrade(
            "myfirstcluster",
            "mychart",
            dict(foo="bar", b=42),
            repo="http://myrepo",
            version="v1.42",
            namespace="mynamespace",
        )

        self.assertEqual([{"foo": "bar"}], result)
        mock_execute.assert_called_once_with(
            "helm",
            "upgrade",
            "myfirstcluster",
            "mychart",
            "--history-max",
            10,
            "--install",
            "--output",
            "json",
            "--timeout",
            "5m",
            "--values",
            "-",
            "--namespace",
            "mynamespace",
            "--repo",
            "http://myrepo",
            "--version",
            "v1.42",
            process_input='{"foo": "bar", "b": 42}',
        )

    @mock.patch.object(utils, "execute")
    def test_install_or_upgrade_oci(self, mock_execute):
        mock_execute.return_value = '[{"foo": "bar"}]', ""

        client = helm.Client()
        result = client.install_or_upgrade(
            "myfirstcluster",
            "oci://localhost:5000/helm-charts/mychart",
            dict(foo="bar", b=42),
            version="v1.42",
            namespace="mynamespace",
        )

        self.assertEqual([{"foo": "bar"}], result)
        mock_execute.assert_called_once_with(
            "helm",
            "upgrade",
            "myfirstcluster",
            "oci://localhost:5000/helm-charts/mychart",
            "--history-max",
            10,
            "--install",
            "--output",
            "json",
            "--timeout",
            "5m",
            "--values",
            "-",
            "--namespace",
            "mynamespace",
            "--version",
            "v1.42",
            process_input='{"foo": "bar", "b": 42}',
        )

    @mock.patch.object(helm.CONF, "capi_helm")
    @mock.patch.object(utils, "execute")
    def test_uninstall_release_works(self, mock_execute, mock_conf):
        mock_execute.return_value = "", ""
        mock_conf.kubeconfig_file = "/etc/magnum/kubeconfig"

        client = helm.Client()
        result = client.uninstall_release(
            "myfirstcluster", namespace="mynamespace"
        )

        self.assertIsNone(result)
        mock_execute.assert_called_once_with(
            "helm",
            "uninstall",
            "myfirstcluster",
            "--timeout",
            "5m",
            "--namespace",
            "mynamespace",
            "--kubeconfig",
            "/etc/magnum/kubeconfig",
        )

    @mock.patch.object(utils, "execute")
    def test_uninstall_release_ignore_not_found(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError(
            stderr="release: not found"
        )

        client = helm.Client()
        result = client.uninstall_release(
            "myfirstcluster", namespace="mynamespace"
        )

        self.assertIsNone(result)

    @mock.patch.object(utils, "execute")
    def test_uninstall_release_raises(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError(
            stderr="oh dear!"
        )
        client = helm.Client()

        self.assertRaises(
            processutils.ProcessExecutionError,
            client.uninstall_release,
            "myfirstcluster",
            namespace="mynamespace",
        )


class TestHelmLock(base.TestCase):

    TEST_SERVER = "https://test:6443"
    TEST_KUBECONFIG_YAML = f"""\
    apiVersion: v1
    clusters:
    - cluster:
        certificate-authority: "cafile"
        server: {TEST_SERVER}
      name: default
    contexts:
    - context:
        cluster: default
        user: default
      name: default
    current-context: default
    kind: Config
    users:
    - name: default
      user:
        client-certificate: "certfile"
        client-key: "keyfile"
    """
    TEST_KUBECONFIG = yaml.safe_load(TEST_KUBECONFIG_YAML)

    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data=TEST_KUBECONFIG_YAML,
    )
    @mock.patch.object(kubernetes.Lease, "delete")
    @mock.patch.object(kubernetes.Lease, "apply")
    @mock.patch.object(kubernetes.Lease, "fetch")
    def test_acquire_new_lock(
        self, fetch_lease, apply_lease, delete_lease, mock_open
    ):

        fetch_lease.return_value = None
        apply_lease.return_value = None
        delete_lease.return_value = None

        with helm.HelmLock("foo", "bar", 1):
            return
        # Unreachable if lock acquisition works
        self.assertTrue(False)

    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data=TEST_KUBECONFIG_YAML,
    )
    @mock.patch.object(kubernetes.Lease, "delete")
    @mock.patch.object(kubernetes.Lease, "apply")
    @mock.patch.object(kubernetes.Lease, "fetch")
    def test_wait_for_lock(
        self, fetch_lease, apply_lease, delete_lease, mock_open
    ):

        now = datetime.datetime.now(tz=datetime.UTC)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        mock_lease = {
            "spec": {
                "acquireTime": now_str,
                "renewTime": now_str,
                "holderIdentity": "foo",
                "leaseDurationSeconds": 2,
            }
        }

        fetch_lease.return_value = mock_lease
        apply_lease.return_value = None
        delete_lease.return_value = None

        with helm.HelmLock("foo", "bar", 3):
            return
        # Unreachable if lock acquisition works
        self.assertTrue(False)

    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data=TEST_KUBECONFIG_YAML,
    )
    @mock.patch.object(kubernetes.Lease, "delete")
    @mock.patch.object(kubernetes.Lease, "apply")
    @mock.patch.object(kubernetes.Lease, "fetch")
    def test_claim_expired_lock(
        self, fetch_lease, apply_lease, delete_lease, mock_open
    ):
        now = datetime.datetime.now(tz=datetime.UTC)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        mock_lease = {
            "spec": {
                "acquireTime": now_str,
                "renewTime": now_str,
                "holderIdentity": "foo",
                "leaseDurationSeconds": 2,
            }
        }

        fetch_lease.return_value = mock_lease
        apply_lease.return_value = None
        delete_lease.return_value = None

        with helm.HelmLock("foo", "bar", timeout_seconds=3):
            pass
        apply_lease.assert_called_once()

    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data=TEST_KUBECONFIG_YAML,
    )
    @mock.patch.object(kubernetes.Lease, "delete")
    @mock.patch.object(kubernetes.Lease, "apply")
    @mock.patch.object(kubernetes.Lease, "fetch")
    def test_timeout_waiting_for_lock(
        self, fetch_lease, apply_lease, delete_lease, mock_open
    ):

        now = datetime.datetime.now(tz=datetime.UTC)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        mock_lease = {
            "spec": {
                "acquireTime": now_str,
                "renewTime": now_str,
                "holderIdentity": "foo",
                "leaseDurationSeconds": 3,
            }
        }

        fetch_lease.return_value = mock_lease
        apply_lease.return_value = None
        delete_lease.return_value = None

        def get_lock():
            with helm.HelmLock("foo", "bar", timeout_seconds=2):
                return

        self.assertRaises(
            helm.HelmLockException,
            get_lock,
        )

    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data=TEST_KUBECONFIG_YAML,
    )
    @mock.patch.object(kubernetes.Lease, "delete")
    @mock.patch.object(kubernetes.Lease, "apply")
    @mock.patch.object(kubernetes.Lease, "fetch")
    def test_lease_update_conflict(
        self,
        fetch_lease,
        apply_lease,
        delete_lease,
        mock_open,
    ):

        now = datetime.datetime.now(tz=datetime.UTC)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        mock_lease = {
            "metadata": {"resourceVersion": "foo"},
            "spec": {
                "acquireTime": now_str,
                "renewTime": now_str,
                "holderIdentity": "bar",
                "leaseDurationSeconds": 3,
            },
        }

        fetch_lease.return_value = mock_lease
        delete_lease.return_value = None

        # Simulate 409 response from k8s API response
        response = mock.Mock()
        response.status_code = 409
        response.reason = "Conflict"
        conflict_error = requests.exceptions.HTTPError(response=response)
        apply_lease.side_effect = conflict_error

        def get_lock():
            with helm.HelmLock("foo", "bar", timeout_seconds=1):
                return

        self.assertRaises(
            helm.HelmLockException,
            get_lock,
        )
