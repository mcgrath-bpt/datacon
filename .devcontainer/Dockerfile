FROM python:3.15.2-slim-bookworm@sha256:4e03260adeeebafccd084f3584e6b84823aba5651cfb53ef8a078ed441ddf9cd AS os-candidate

# This intermediate target produces review candidates, never a qualified workspace.
COPY requirements/os/debian.sources /etc/apt/sources.list.d/debian.sources
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates git openssh-client postgresql-client make less \
    && rm -rf /var/lib/apt/lists/*

FROM os-candidate AS os-locked
COPY requirements/os /opt/datacon/requirements/os
COPY scripts/verify_os.py /opt/datacon/scripts/verify_os.py
RUN python /opt/datacon/scripts/verify_os.py

FROM os-locked AS workspace
COPY requirements/workspace.txt /opt/datacon/requirements/workspace.txt
RUN python -m venv /opt/datacon/venv \
    && /opt/datacon/venv/bin/pip install --no-cache-dir --only-binary=:all: --require-hashes \
       -r /opt/datacon/requirements/workspace.txt \
    && /opt/datacon/venv/bin/pip check

RUN groupadd --gid 1000 developer \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash developer \
    && mkdir -p /workspaces \
    && chown developer:developer /workspaces

COPY scripts /opt/datacon/scripts
COPY platform /opt/datacon/platform
COPY docs /opt/datacon/docs
COPY AGENTS.md README.md PLAN.md BACKLOG.md CONTRIBUTING.md HANDOVER.md .python-version /opt/datacon/
ENV PATH="/opt/datacon/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONNOUSERSITE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
USER developer
WORKDIR /workspaces
CMD ["sleep", "infinity"]
