"""
Integration Tests: Kubernetes (K8s) Manifest Validation & Cluster Deployment
"""

import os
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
K8S_DIR = PROJECT_ROOT / "k8s"


@pytest.mark.integration
class TestKubernetesDeployment:
    """Tests Kubernetes manifests and live cluster interaction."""

    def test_k8s_directory_and_kustomization_exist(self):
        assert K8S_DIR.exists(), "k8s directory does not exist"
        assert (K8S_DIR / "kustomization.yaml").exists(), "k8s/kustomization.yaml not found"
        assert (K8S_DIR / "namespace.yaml").exists(), "k8s/namespace.yaml not found"

    def test_kubectl_dry_run_validation(self):
        """Validates all Kubernetes manifests using kubectl client-side dry run."""
        res = subprocess.run(
            ["kubectl", "apply", "--dry-run=client", "-k", str(K8S_DIR)],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"kubectl dry-run failed with error:\n{res.stderr}"
        assert "namespace/" in res.stdout or "deployment.apps/" in res.stdout

    def test_k8s_live_cluster_apply(self):
        """Tests live deployment to Kubernetes cluster if cluster is available."""
        cluster_check = subprocess.run(["kubectl", "cluster-info", "--request-timeout=2s"], capture_output=True)
        if cluster_check.returncode != 0:
            pytest.skip("No live Kubernetes cluster available for live apply test.")

        # Apply manifests to cluster
        apply_res = subprocess.run(
            ["kubectl", "apply", "-k", str(K8S_DIR)],
            capture_output=True,
            text=True
        )
        assert apply_res.returncode == 0, f"Failed to apply K8s resources: {apply_res.stderr}"

        # Verify deployments exist in namespace
        namespace = f"stack-{PROJECT_ROOT.name}"
        get_res = subprocess.run(
            ["kubectl", "get", "deployments", "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True
        )
        assert get_res.returncode == 0, f"Failed to get deployments in namespace {namespace}"
        assert '"items"' in get_res.stdout
