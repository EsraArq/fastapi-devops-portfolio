Keep the FastAPI app stateless and preserve /livez, /readyz, and /metrics.
Run python -m pytest -q and kubectl kustomize k8s before proposing changes.
Keep Kubernetes containers non-root with read-only filesystems and resource limits.
Never add credentials, raw headers, query strings, or user data to logs or metric labels.
Keep release permissions scoped to the main-branch release job. Argo CD pulls immutable image digests from deploy.
