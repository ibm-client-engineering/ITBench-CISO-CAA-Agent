# CISO Agent

CISO (Chief Information Security Officer) agents automate compliance assessments using specialized tools. They generate policies (e.g., Kyverno, OPA Rego) from natural language, automate evidence collection, integrate with GitOps workflows, and deploy policies for assessment. Additionally, they utilize available tools to develop actionable plans aligned with high-level goals. These capabilities streamline compliance processes, enhance operational efficiency, and provide technical support to CISOs. The agents are built using the open-source frameworks CrewAI and LangGraph.

## Installation

### 1. Install the project and dependencies

```bash
$ pip install -e .
```

### 2. (OPTIONAL) Set up Langtrace instance

You can use LangTrace to record & check LLM interactions.

Follow the doc [here](./langtrace.md) for setup.

### 3. Create `.env` file and set credentials

Create `.env` file in the root dir of this project like the following.

Please use your own keys for `OPENAI_API_KEY` and `LANGTRACE_API_KEY`.

```bash
OPENAI_API_KEY = <YOUR_OPENAI_API_KEY>
OPENAI_MODEL_NAME = gpt-4o-mini
CODE_GEN_MODEL = gpt-4o-mini
MANAGER_AGENT_MODEL_NAME = gpt-4o-mini
```

### 4. Prepare environment with bundle

Follow the doc of [caa-task-scenarios](https://github.ibm.com/project-polaris/caa-task-scenarios).

Complete `make deploy_bundle` and `make inject_fault` for the scenario.

(Use `bundles/cis-b-gen/cis-b.5.1.1-gen`, the Kyverno gen scenario for 5.1.1, as an example in this doc)

### 5. Run the demo

Run main.py with a goal statement for each scenario.

The example command below is for the Kyverno gen scenario for 5.1.1.

```bash
$ python src/ciso_agent/main.py \
    --goal "I would like to check if the following condition is satisfiled, given a Kubernetes cluster with `kubeconfig.yaml`
    Ensure that the cluster-admin role is only used where required

To check the condition, do the following steps.
- deploy a Kyverno policy to the cluster
- chcek if the policy is correctly deployed.

If deploying the policy failed and if you can fix the issue, you will do it and try deploying again.
Once you get a final answer, you can quit the work.

The cluster's kubeconfig is at `/tmp/kubeconfig.yaml`.
" \
--output /tmp/test-workdir/result.json
```

To check the result, you can do `make evaluate` in the bundle dir.
