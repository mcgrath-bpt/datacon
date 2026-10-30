FROM python:3.14.8-slim-bookworm@sha256:44e000a07b48bef1517a2b14adc93c17af728ca98858b5e24c6e1b18de1b2ef2

# No OS package installation: the complete OS is inherited from this digest.
COPY requirements/toolchain.txt /opt/datacon/requirements/toolchain.txt
RUN python -m venv /opt/datacon/venv \
    && /opt/datacon/venv/bin/pip install --no-cache-dir --only-binary=:all: --require-hashes \
       -r /opt/datacon/requirements/toolchain.txt \
    && /opt/datacon/venv/bin/pip check

ARG WORKSPACE_UID=1000
ARG WORKSPACE_GID=1000
RUN test "$WORKSPACE_UID" -gt 0 && test "$WORKSPACE_GID" -gt 0 \
    && groupadd --gid "$WORKSPACE_GID" developer \
    && useradd --uid "$WORKSPACE_UID" --gid "$WORKSPACE_GID" --create-home developer \
    && mkdir -p /workspaces && chown developer:developer /workspaces
COPY scripts /opt/datacon/scripts
COPY platform /opt/datacon/platform
COPY requirements /opt/datacon/requirements
COPY .devcontainer/Dockerfile /opt/datacon/.devcontainer/Dockerfile
COPY containers/toolchain/Dockerfile /opt/datacon/containers/toolchain/Dockerfile
COPY compose.yaml /opt/datacon/compose.yaml
COPY containers/postgres /opt/datacon/containers/postgres
COPY .python-version datacon /opt/datacon/
RUN python /opt/datacon/scripts/baseline.py > /opt/datacon/baseline.json
ENV PATH="/opt/datacon/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GX_ANALYTICS_ENABLED=false OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
USER developer
WORKDIR /workspaces
CMD ["python", "/opt/datacon/scripts/toolchain_smoke.py"]
