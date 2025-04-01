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

from unittest import mock

from magnum.common import utils
from oslo_concurrency import processutils

from magnum_capi_helm import helm
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
    def test_install_or_upgrade_noversion(self, mock_execute):
        mock_execute.return_value = '[{"foo": "bar"}]', ""

        client = helm.Client()
        result = client.install_or_upgrade(
            "myfirstcluster",
            "mychart",
            dict(foo="bar", b=42),
            repo="http://myrepo",
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
            process_input='{"foo": "bar", "b": 42}',
        )

    # Apply update and handle a Helm update conflict.
    # We will throw an exception, which should be caught.
    # and get an empty result back.
    @mock.patch.object(utils, "execute")
    def test_install_or_upgrade_conflict(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError(
            stderr="Error: UPGRADE FAILED: another operation "
            "(install/upgrade/rollback) is in progress"
        )

        client = helm.Client()
        result = client.install_or_upgrade(
            "myfirstcluster",
            "mychart",
            dict(foo="bar", b=42),
            repo="http://myrepo",
            version="v1.42",
            namespace="mynamespace",
        )

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
        self.assertEqual(result, {})

    @mock.patch.object(utils, "execute")
    def test_install_or_upgrade_conflict_2(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError(
            stderr="Error: UPGRADE FAILED: release: already exists"
        )

        client = helm.Client()
        result = client.install_or_upgrade(
            "myfirstcluster",
            "mychart",
            dict(foo="bar", b=42),
            repo="http://myrepo",
            version="v1.42",
            namespace="mynamespace",
        )

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
        self.assertEqual(result, {})

    @mock.patch.object(utils, "execute")
    def test_install_or_upgrade_conflict_3(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError(
            stderr="Error: UPGRADE FAILED: other unexpected error"
        )

        client = helm.Client()
        result = client.install_or_upgrade(
            "myfirstcluster",
            "mychart",
            dict(foo="bar", b=42),
            repo="http://myrepo",
            version="v1.42",
            namespace="mynamespace",
        )

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
        self.assertEqual(result, {})

    # Test pending update when the chart release is not found.
    # An exception should be raised and handled.
    @mock.patch.object(utils, "execute")
    def test_update_pending_notfound(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError(
            stderr="release: not found"
        )

        client = helm.Client()
        result = client.update_pending(
            "myfirstcluster",
            "0.10.2",
            "openstack-test-chart",
            dict(foo="bar", b=42),
            namespace="magnum-1231023942304982304",
        )

        self.assertEqual(True, result)
        mock_execute.assert_called_once_with(
            "helm",
            "get",
            "metadata",
            "--namespace",
            "magnum-1231023942304982304",
            "myfirstcluster",
            "--output",
            "json",
        )

    @mock.patch.object(utils, "execute")
    def test_update_pending(self, mock_execute):
        mock_execute.return_value = (
            '{"name":"mynamespace","chart":"openstack-test-chart",'
            '"version":"0.10.1","appVersion":"abc123",'
            '"namespace":"magnum-1231023942304982304","revision":2,'
            '"status":"deployed","deployedAt":"2025-01-01T10:10:10Z"}',
            "",
        )

        client = helm.Client()
        result = client.update_pending(
            "myfirstcluster",
            "0.10.2",
            "openstack-test-chart",
            dict(foo="bar", b=42),
            namespace="magnum-1231023942304982304",
        )

        self.assertEqual(True, result)
        mock_execute.assert_called_once_with(
            "helm",
            "get",
            "metadata",
            "--namespace",
            "magnum-1231023942304982304",
            "myfirstcluster",
            "--output",
            "json",
        )

    @mock.patch.object(utils, "execute")
    def test_update_pending_incomplete_meta(self, mock_execute):
        mock_execute.return_value = (
            '{"name":"mynamespace","chart":"openstack-test-chart",'
            '"namespace":"magnum-1231023942304982304","status":"deployed",'
            '"deployedAt":"2025-01-01T10:10:10Z"}',
            "",
        )

        client = helm.Client()
        result = client.update_pending(
            "myfirstcluster",
            "0.10.2",
            "openstack-test-chart",
            dict(foo="bar", b=42),
            namespace="magnum-1231023942304982304",
        )

        self.assertEqual(True, result)
        mock_execute.assert_called_once_with(
            "helm",
            "get",
            "metadata",
            "--namespace",
            "magnum-1231023942304982304",
            "myfirstcluster",
            "--output",
            "json",
        )

    # Bump the chart version: update needed
    @mock.patch.object(utils, "execute")
    def test_update_pending_mismatch_version(self, mock_execute):
        mock_execute.return_value = (
            '{"name": "mynamespace", "chart": "openstack-test-chart",'
            '"version": "0.10.1", "appVersion": "abc123",'
            '"namespace": "magnum-1231023942304982304", "revision": 2,'
            '"status": "deployed",'
            '"deployedAt": "2025-01-01T10:10:10Z"}',
            "",
        )

        client = helm.Client()
        result = client.update_pending(
            "myfirstcluster",
            "0.11.2",
            "openstack-test-chart",
            dict(foo="bar", b=42),
            namespace="magnum-1231023942304982304",
        )

        self.assertEqual(True, result)
        mock_execute.assert_called_once_with(
            "helm",
            "get",
            "metadata",
            "--namespace",
            "magnum-1231023942304982304",
            "myfirstcluster",
            "--output",
            "json",
        )

    # Test pending update when the chart values match
    @mock.patch.object(utils, "execute")
    def test_update_pending_values_nochange(self, mock_execute):
        mock_execute.side_effect = [
            # Output from first call to mock_execute
            (
                '{"name": "mynamespace", "chart": "openstack-test-chart",'
                '"version": "0.10.1", "appVersion": "abc123",'
                '"namespace": "magnum-1231023942304982304", "revision": 2,'
                '"status": "deployed",'
                '"deployedAt": "2025-01-01T10:10:10Z"}',
                "",
            ),
            # Output from second call to mock_execute
            (
                '{"addons": { "ingress": {"enabled": false}},'
                '"apiServer":{"enableLoadBalancer": true},'
                '"kubernetesVersion": "1.31.2",'
                '"nodeGroups":[]}',
                "",
            ),
        ]

        client = helm.Client()
        result = client.update_pending(
            "myfirstcluster",
            "0.10.1",
            "openstack-test-chart",
            dict(
                addons=dict(ingress=dict(enabled=False)),
                apiServer=dict(enableLoadBalancer=True),
                kubernetesVersion="1.31.2",
                nodeGroups=[],
            ),
            namespace="magnum-1231023942304982304",
        )

        self.assertEqual(False, result)
        self.assertEqual(mock_execute.call_count, 2)

    # Test pending update when the chart values don't match
    @mock.patch.object(utils, "execute")
    def test_update_pending_values_change(self, mock_execute):
        mock_execute.side_effect = [
            (
                '{"name": "mynamespace", "chart": "openstack-test-chart",'
                '"version": "0.10.1", "appVersion": "abc123",'
                '"namespace": "magnum-1231023942304982304", "revision": 2,'
                '"status": "deployed",'
                '"deployedAt": "2025-01-01T10:10:10Z"}',
                "",
            ),
            (
                '{"addons": { "ingress": {"enabled": false}},'
                '"apiServer":{"enableLoadBalancer": true},'
                '"kubernetesVersion": "1.31.2",'
                '"nodeGroups":[{"machineCount":2,"machineFlavor":"medium",'
                '"name":"worker-ng"}]}',
                "",
            ),
        ]

        client = helm.Client()
        result = client.update_pending(
            "myfirstcluster",
            "0.10.1",
            "openstack-test-chart",
            dict(
                addons=dict(ingress=dict(enabled=False)),
                apiServer=dict(enableLoadBalancer=True),
                kubernetesVersion="1.31.2",
                nodeGroups=[],
            ),
            namespace="magnum-1231023942304982304",
        )

        self.assertEqual(True, result)
        self.assertEqual(mock_execute.call_count, 2)

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
