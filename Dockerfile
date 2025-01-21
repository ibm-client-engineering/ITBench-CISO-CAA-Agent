# User `bench-server` as a base image here
# because it is a minimum image of agent-bench-automation codes
FROM bench-server:latest

# need unzip for `aws` command
RUN apt update -y && apt install -y unzip

RUN mkdir /etc/ciso-agent
COPY src /etc/ciso-agent/src
COPY pyproject.toml /etc/ciso-agent/pyproject.toml
COPY agent-harness.yaml /etc/ciso-agent/agent-harness.yaml

WORKDIR /etc/ciso-agent
RUN python -m venv .venv && source .venv/bin/activate && pip install -e /etc/ciso-agent --no-cache-dir

# install `ansible-playbook`
RUN source .venv/bin/activate && pip install ansible-core jmespath kubernetes --no-cache-dir
RUN source .venv/bin/activate && ansible-galaxy collection install kubernetes.core
# install `jq`
RUN apt update -y && apt install -y jq
# install `kubectl`
RUN curl -LO https://dl.k8s.io/release/v1.31.0/bin/linux/$(dpkg --print-architecture)/kubectl && \
    chmod +x ./kubectl && \
    mv ./kubectl /usr/local/bin/kubectl
# install `aws` (need this for using kubectl against AWS cluster)
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install
# install `opa`
RUN curl -L -o opa https://github.com/open-policy-agent/opa/releases/download/v1.0.0/opa_linux_$(dpkg --print-architecture)_static && \
    chmod +x ./opa && \
    mv ./opa /usr/local/bin/opa

# Agent is executed by agent-harness of agent-bench-automation, so workdir should be agent-benchmark
WORKDIR /etc/agent-benchmark
