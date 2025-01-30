# CISO Agent

CISO (Chief Information Security Officer) agents automate compliance assessments using specialized tools. They generate policies (e.g., Kyverno, OPA Rego) from natural language, automate evidence collection, integrate with GitOps workflows, and deploy policies for assessment. Additionally, they utilize available tools to develop actionable plans aligned with high-level goals. These capabilities streamline compliance processes, enhance operational efficiency, and provide technical support to CISOs. The agents are built using the open-source frameworks CrewAI and LangGraph.


## Prerequisites

- `python` command (3.11 or later)
- [Sample Task Scenario](https://github.ibm.com/DistributedCloudResearch/sample-task-scenarios.git) setup
  - This requires 1 Kubernetes cluster and/or 1 RHEL host. For more details, please refer to its README.

## Getting started

### 1. Setup a Sample Task Scenario on your Kubernetes cluster / RHEL host

Follow the README and complete `make deploy_bundle` and `make inject_fault` commands for a single scenario.

Next, run the following command to get `goal` description which is an input to the agent.

```bash
$ make get 2>/dev/null | jq -r .goal_template
```

Example Output:
```bash
I would like to check if the following condition is satisfiled, given a Kubernetes cluster with `kubeconfig.yaml`
    Minimize the admission of containers wishing to share the host network namespace.

To check the condition, do the following steps.
- deploy a Kyverno policy to the cluster
- chcek if the policy is correctly deployed.

If deploying the policy failed and if you can fix the issue, you will do it and try deploying again.
Once you get a final answer, you can quit the work.

The cluster's kubeconfig is at `{{ kubeconfig }}`.
```

The above text is an example of ciso task scenarios.

To provide this as input to the agent, ensure your kubeconfig file is available at a specific location in your machine and replace `{{ kubeconfig }}` with its actual file path.


### 2. Clone this repository

```bash
$ git clone https://github.ibm.com/project-polaris/ciso-agent.git
$ cd ciso-agent

# [OPTIONAL] Create a virtual environment for python

$ pip install -e .
```

### 3. Create `.env` file and set credentials

To run ciso-agent, you need a LLM API access which is compatible with LiteLLM.

Many LLM services support it, including IBM watsonx.ai, OpenAI and Azure OpenAI Service.

To configure access, create a .env file in the root directory of ciso-agent with the following details.

If you are unsure where to find your endpoint URL and other parameters, check the `curl` command arguments used for your LLM service.

i. For **IBM watsonx.ai**

```bash
# .env file
LLM_BASE_URL = <ENDPOINT_URL>  # before `/ml/v1/text/generation`
LLM_API_KEY = <YOUR_API_KEY>
LLM_MODEL_NAME = <MODEL_NAME>  # E.g. "ibm/granite-3-8b-instruct"
WATSONX_PROJECT_ID = <YOUR_WATSONX_PROJECT_ID>
```

ii. For **OpenAI**
```bash
# .env file
LLM_API_KEY = <YOUR_API_KEY>
LLM_MODEL_NAME = <MODEL_NAME>  # E.g. "gpt-4o-mini"
# NOTE: The endpoint URL an be omitted for OpenAI
```

iii. For **Azure OpenAI Service**
```bash
# .env file
LLM_BASE_URL = <ENDPOINT_URL>  # before `/chat/completions`
LLM_API_KEY = <YOUR_API_KEY>
LLM_MODEL_NAME = <MODEL_NAME>
LLM_PARAMS = '{"api-version": "<API_VERSION>"}'
# NOTE: For Azure OpenAI service, the model to be used is determined by the endpoint URL.
#       Thus, <MODEL_NAME> here is ignored during LLM calls.
```


### 4. Start the agent

Now, ready to run the agent.
Please run the following command to start agent with goal description text which is obtained at the step 1.

```bash
$ python src/ciso_agent/main.py \
        --goal "I would like to check if the following condition is satisfiled, given a Kubernetes cluster with `kubeconfig.yaml`
    Minimize the admission of containers wishing to share the host network namespace.

To check the condition, do the following steps.
- deploy a Kyverno policy to the cluster
- chcek if the policy is correctly deployed.

If deploying the policy failed and if you can fix the issue, you will do it and try deploying again.
Once you get a final answer, you can quit the work.

The cluster's kubeconfig is at `/tmp/agent/20250122154450/kubeconfig.yaml`.
You can use `/tmp/agent/20250122154450/` as your workdir." \
        --auto-approve
```

NOTE: In this example, the bottom line to tell agent where is its work directory is added.

### 5. Evaluation

Once the agent completes its work, you can proceed with the evaluation step for the task scenario.

Please refer to the README of the task scenario for further details.
