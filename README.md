# CISO Agent

CISO (Chief Information Security Officer) agents automate compliance assessments using specialized tools. They generate policies (e.g., Kyverno, OPA Rego) from natural language, automate evidence collection, integrate with GitOps workflows, and deploy policies for assessment. Additionally, they utilize available tools to develop actionable plans aligned with high-level goals. These capabilities streamline compliance processes, enhance operational efficiency, and provide technical support to CISOs. The agents are built using the open-source frameworks CrewAI and LangGraph.


## Prerequisites

- `python` command (3.11 or later)
- `kind` command
- running `IT Bench` service ([Reference](https://github.ibm.com/project-polaris/agent-bench-automation.git))

## Getting started

**NOTE: Step 1 to 4 below are necessary only for the first time**

### 1. Clone the repositories

```bash
$ mkdir <YOUR_WORKSPACE>
$ cd <YOUR_WORKSPACE>

$ git clone https://github.ibm.com/project-polaris/agent-bench-automation.git
$ git clone https://github.ibm.com/project-polaris/ciso-agent.git
```

### 2. Create python venv for the 2 applications

For agent-bench-automation
```bash
$ cd agent-bench-automation
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
$ cd ..
```

For ciso-agent
```bash
$ cd ciso-agent
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
$ cd ..
```

### 3. Create `.env` file and set credentials

Create `.env` file in the root dir of `ciso-agent` like the following.

Please use your own keys for `OPENAI_API_KEY` and `LANGTRACE_API_KEY`.

```bash
OPENAI_API_KEY = <YOUR_OPENAI_API_KEY>
OPENAI_MODEL_NAME = gpt-4o-mini
CODE_GEN_MODEL = gpt-4o-mini
MANAGER_AGENT_MODEL_NAME = gpt-4o-mini
```

### 4. Prepare an Ingress-ready Kind cluster

```bash
$ cd agent-bench-automation
$ kind create cluster --name minibench --config helm/ingress-kind-config.yaml
Creating cluster "minibench" ...
 ✓ Ensuring node image (kindest/node:v1.31.0) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-minibench"
You can now use your cluster with:

kubectl cluster-info --context kind-minibench

Not sure what to do next? 😅  Check out https://kind.sigs.k8s.io/docs/user/quick-start/
```

### 5. Create an agent and a benchmark on IT Bench Web UI

#### 5.1 Create an agent

#### 5.2 Create an benchmark for the agent

#### 5.3 Get agent manifest

### 6. Run Agent API Server via Helm

```bash
$ cd agent-bench-automation
$ cd helm
$ helm install minibench-server minibench-server/
```

### 7. Start the agent

```bash
$ cd agent-bench-automation
$ PYTHONUNBUFFERED=1 \
python agent_bench_automation/agent_harness/main.py \
    --agent_directory ../ciso-agent \
    -i ./docs/scenario-support/agent-manifest.json \
    -c ./docs/scenario-support/agent-harness.yaml \
    --host <HOSTNAME_OF_IT_BENCH_SERVICE> \
    --port <PORT_NUM_OF_IT_BENCH_SERVICE> \
    --ssl
```
