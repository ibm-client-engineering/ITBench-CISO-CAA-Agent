# Copyright (c) 2025 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import re
import subprocess
from typing import Callable, Union

from caa_agent.llm import call_llm, extract_code
from crewai_tools import BaseTool
from pydantic import BaseModel, Field


class GeneratePlaybookToolInput(BaseModel):
    sentence: Union[str, dict] = Field(
        description=(
            "A short description of Ansible Playbook to be generated. This includes the compliance requirement. "
            "This includes what is accomplished with the Playbook execution."
        )
    )
    playbook_file: str = Field(description="A filepath for the Playbook to be saved.", default="playbook.yml")


class GeneratePlaybookTool(BaseTool):
    name: str = "GeneratePlaybookTool"
    # correct description
    description: str = "The tool to generate a Playbook. This tool returns the generated Playbook."

    args_schema: type[BaseModel] = GeneratePlaybookToolInput

    # disable cache
    cache_function: Callable = lambda _args, _result: False

    workdir: str = ""

    def __init__(self, **kwargs):
        super_args = {k: v for k, v in kwargs.items() if k not in ["workdir"]}
        super().__init__(**super_args)
        if "workdir" in kwargs:
            self.workdir = kwargs["workdir"]

    def _run(self, sentence: Union[str, dict], playbook_file: str = "playbook.yml") -> str:
        print("GeneratePlaybookTool is called")
        spec = sentence
        if isinstance(spec, dict):
            try:
                spec = json.dumps(spec, indent=2)
            except Exception:
                pass
        prompt = f"""Generate a very simple Ansible Playbook to do the following:
{spec}


Points:
- You should save a detailed info. Not a boolean of the check result.
- To read/write OS level files (e.g. under `/etc` dir), you should add `become: true`. Use grep.
- Do not use `setup` module.
- To save a variable in the playbook, you can use this task.
    ```yaml
    - name: Save a variable content in a localhost
      copy:
        content: {{{{ variable_name | quote }}}}
        dest: collected_data.json
      delegate_to: localhost
      become: false
    ```
  If you try to save a registered variable, do not parse it. Just save it as is.
  `become: false` is necessary for this task because you don't have sudo permission on localhost.
  Use "collected_data.json" and do not change the destination file name.
- Do not try to find "collected_data.json" when not found. Just collect the data again.
- Do not specify absolute path anywhere. You must use the current directory.
- If you need command result as a collected data, you should add `ignore_errors: true` to the task.
- Use Ansible module instead of command, if possible.
"""
        model = os.getenv("CODE_GEN_MODEL")
        api_key = os.getenv("CODE_GEN_API_KEY")
        print(f"Generating Playbook code with '{model}'")
        print("Prompt:", prompt)
        answer = call_llm(prompt, model=model, api_key=api_key)
        code = extract_code(answer, code_type="yaml")
        playbook_file = playbook_file.strip('"').strip("'").lstrip("{").rstrip("}")
        if not playbook_file:
            playbook_file = "playbook.yaml"
        fpath = os.path.join(self.workdir, playbook_file)
        with open(fpath, "w") as f:
            f.write(code)
        print("Code in answer:", code)
        return code


class RunPlaybookToolInput(BaseModel):
    host: str = Field(description="The hostname where the Playbook should be executed")
    playbook_file: str = Field(description="Playbook filepath to be run")


class RunPlaybookTool(BaseTool):
    name: str = "RunPlaybookTool"
    # correct description
    description: str = """The tool to run a playbook on a given host.
This tool returns the following:
  - return_code: if 0, the command was successful, otherwise, failure.
  - stdout: standard output of the command
  - stderr: standard error of the command (only when error occurred)
"""

    args_schema: type[BaseModel] = RunPlaybookToolInput

    # disable cache
    cache_function: Callable = lambda _args, _result: False

    workdir: str = ""

    def __init__(self, **kwargs):
        super_args = {k: v for k, v in kwargs.items() if k not in ["workdir"]}
        super().__init__(**super_args)
        if "workdir" in kwargs:
            self.workdir = kwargs["workdir"]

    def _run(self, host: str, playbook_file: str) -> str:
        print("RunPlaybookTool is called")

        code = ""
        fpath = os.path.join(self.workdir, playbook_file)
        with open(fpath, "r") as f:
            code = f.read()
        lines = code.splitlines()
        for i, line in enumerate(lines):
            if line.strip().lstrip("- ").startswith("hosts"):
                new_line = re.sub("hosts: .*", f"hosts: {host}", line)
                lines[i] = new_line
        code = "\n".join(lines) + "\n"
        with open(fpath, "w") as f:
            f.write(code)

        print("[DEBUG] Running this playbook:", code)

        cmd_str = f"ansible-playbook {playbook_file} -i inventory.ansible.ini"
        proc = subprocess.run(
            cmd_str,
            shell=True,
            cwd=self.workdir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print("[DEBUG] ansible-playbook result returncode:", proc.returncode)
        print("[DEBUG] ansible-playbook result stdout:", proc.stdout)
        print("[DEBUG] ansible-playbook result stderr:", proc.stderr)
        # if proc.returncode != 0:
        #     raise ValueError(f"failed to run a playbook; stdout: {proc.stdout}, stderr: {proc.stderr}")
        result = {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
        }
        if proc.returncode != 0:
            result["stderr"] = proc.stderr
        return result


class GenerateOPARegoToolInput(BaseModel):
    sentence: Union[str, dict] = Field(
        description="A short description of OPA Rego policy to be generated. This includes what is validated with the Rego policy evaluation."
    )
    policy_file: str = Field(description="A filepath for the Rego policy to be saved.")
    input_file: str = Field(description="The filepath to the input data to be used for checking the policy.")


class GenerateOPARegoTool(BaseTool):
    name: str = "GenerateOPARegoTool"
    # correct description
    description: str = "The tool to generate an OPA Rego policy. This tool returns the generated Rego policy."

    args_schema: type[BaseModel] = GenerateOPARegoToolInput

    # disable cache
    cache_function: Callable = lambda _args, _result: False

    workdir: str = ""

    def __init__(self, **kwargs):
        super_args = {k: v for k, v in kwargs.items() if k not in ["workdir"]}
        super().__init__(**super_args)
        if "workdir" in kwargs:
            self.workdir = kwargs["workdir"]

    def _run(self, sentence: Union[str, dict], policy_file: str, input_file: str) -> str:
        print("GenerateOPARegoTool is called")
        spec = sentence
        if isinstance(spec, dict):
            try:
                spec = json.dumps(spec, indent=2)
            except Exception:
                pass
        prompt = f"""Generate a very simple OPA Rego policy to evaluate the following condition:
    {spec}
"""
        if input_file:
            input_data = ""
            fpath = os.path.join(self.workdir, input_file)

            if not os.path.exists(fpath):
                raise OSError(f"input_file `{input_file}` is not found. This file must be prepared beforehand.")

            with open(fpath, "r") as f:
                input_data = f.read()

            truncated_msg = ""
            # truncate input_data to avoid too long input token
            if len(input_data) > 1000:
                input_data = input_data[:1000]
                truncated_msg = "\n(original data is too long, so truncated here)"
            prompt += f"""
Input data to be evaluated:
```json
{input_data}
{truncated_msg}
```
"""
        prompt += """

Points:
- `input` in your code is the above "Input data"
- If input data is just a string, check string match
- If input data is truncated, assume the data contents
- the final output must be `result`
- when input data should be disallowed, `result` must be `false`
- the package name must be `check`
- always insert `import rego.v1` after `package check`
- OPA is case sensitive. "False" and "false" is different.
- when error says "`if` keyword is required before rule body", you should change the code
  from something like `result := false {}` to `result := false if {}`
- The following is an example of a OPA Rego policy to disallow input if any item's value contains "ab"
```rego
package check
import rego.v1

default result := true

result := false if {
    some i
    contains(input.items[i].value, "ab")
}
```

for this example input data.
```json
{
    "items": [
        {"value": "abc"},
        {"value": "def"}
    ]
}
```
"""

        model = os.getenv("CODE_GEN_MODEL")
        api_key = os.getenv("CODE_GEN_API_KEY")
        print(f"Generating OPA Rego policy code with '{model}'")
        print("Prompt:", prompt)
        answer = call_llm(prompt, model=model, api_key=api_key)
        code = extract_code(answer, code_type="rego")
        policy_file = policy_file.strip('"').strip("'").lstrip("{").rstrip("}")
        if not policy_file:
            policy_file = "policy.rego"
        opath = os.path.join(self.workdir, policy_file)
        with open(opath, "w") as f:
            f.write(code)
        print("Code in answer:", code)
        return code


class RunOPARegoToolInput(BaseModel):
    policy_file: str = Field(description="Rego policy filepath to be evaluated")
    input_file: str = Field(description="The filepath to the input data to be used for checking the policy")


class RunOPARegoTool(BaseTool):
    name: str = "RunOPARegoTool"
    # correct description
    description: str = "The tool to run OPA Rego evaluation. This tool returns the check result."

    args_schema: type[BaseModel] = RunOPARegoToolInput

    # disable cache
    cache_function: Callable = lambda _args, _result: False

    workdir: str = ""

    def __init__(self, **kwargs):
        super_args = {k: v for k, v in kwargs.items() if k not in ["workdir"]}
        super().__init__(**super_args)
        if "workdir" in kwargs:
            self.workdir = kwargs["workdir"]

    def _run(self, policy_file: str, input_file: str) -> str:
        print("RunOPARegoTool is called")
        fpath = os.path.join(self.workdir, policy_file)
        rego_pkg_name = get_rego_main_package_name(rego_path=fpath)
        if not rego_pkg_name:
            raise ValueError("`package` must be defined in the rego policy file")

        input_data = ""
        ipath = os.path.join(self.workdir, input_file)
        with open(ipath, "r") as f:
            input_data = f.read()

        cmd_str = f"opa eval --data {policy_file} --stdin-input 'data.{rego_pkg_name}'"
        proc = subprocess.run(
            cmd_str,
            shell=True,
            cwd=self.workdir,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        input_data_to_show = input_data
        truncated_msg = ""
        if len(input_data_to_show) > 1000:
            input_data_to_show = input_data_to_show[:1000]
            truncated_msg = " (truncated)"
        print(f"command: {cmd_str}")
        print(f"proc.input_data{truncated_msg}: {input_data_to_show}")
        print(f"proc.stdout: {proc.stdout}")
        print(f"proc.stderr: {proc.stderr}")

        if proc.returncode != 0:
            error = f"failed to run `opa eval` command; error details:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
            raise ValueError(error)

        result = json.loads(proc.stdout)
        if "result" not in result:
            raise ValueError(f"`result` field does not exist in the output from `opa eval` command; raw output: {proc.stdout}")

        result_arr = result["result"]
        if not result_arr:
            raise ValueError(f"`result` field in the output from `opa eval` command has no contents; raw output: {proc.stdout}")

        first_result = result_arr[0]
        if not first_result and "expressions" not in first_result:
            raise ValueError(
                f"`expressions` field does not exist in the first result of output from `opa eval` command; first_result: {first_result}"
            )

        expressions = first_result["expressions"]
        if not expressions:
            raise ValueError(f"`expressions` field in the output from `opa eval` command has no contents; first_result: {first_result}")

        expression = expressions[0]
        result_value = expression.get("value", {})
        eval_result = {
            "value": result_value,
            "message": proc.stderr,
        }
        print(eval_result)
        return eval_result


def get_rego_main_package_name(rego_path: str):
    pkg_name = ""
    with open(rego_path, "r") as file:
        prefix = "package "
        for line in file:
            _line = line.strip()
            if _line.startswith(prefix):
                pkg_name = _line[len(prefix) :]
                break
    return pkg_name


class GenerateKyvernoToolInput(BaseModel):
    sentence: Union[str, dict] = Field(
        description="A short description of Kyverno policy to be generated. This includes what is validated with the Kyverno policy."
    )
    policy_file: str = Field(description="filepath for the Kyverno policy to be saved.")
    current_policy_file: str = Field(
        description="filepath of the current Kyverno policy to be updated. Only needed when updating an existing policy", default=""
    )


class GenerateKyvernoTool(BaseTool):
    name: str = "GenerateKyvernoTool"
    # correct description
    description: str = (
        "The tool to generate a Kyverno policy. This tool returns the generated Kyverno policy. "
        "This can be used for updating existing Kyverno policy."
    )

    args_schema: type[BaseModel] = GenerateKyvernoToolInput

    # disable cache
    cache_function: Callable = lambda _args, _result: False

    workdir: str = ""

    def __init__(self, **kwargs):
        super_args = {k: v for k, v in kwargs.items() if k not in ["workdir"]}
        super().__init__(**super_args)
        if "workdir" in kwargs:
            self.workdir = kwargs["workdir"]

    def _run(self, sentence: Union[str, dict], policy_file: str, current_policy_file: str = "") -> str:
        print("GenerateKyvernoTool is called")
        spec = sentence
        if isinstance(spec, dict):
            try:
                spec = json.dumps(spec, indent=2)
            except Exception:
                pass

        current_policy_block = ""
        if current_policy_file:
            current_policy = ""
            fpath = os.path.join(self.workdir, current_policy_file)
            with open(fpath, "r") as f:
                current_policy = f.read()
            current_policy_block = f"""Please update the following current policy:
```yaml
{current_policy}
```

"""

        prompt = f"""Generate a very simple Kyverno policy to do the following:
{spec}

{current_policy_block}

---
The following is an example of a Kyverno Policy to disallow Pod creation in `default` namespace
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-default-namespace
spec:
  rules:
  - name: validate-namespace
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Using 'default' namespace is not allowed."
      pattern:
        metadata:
          namespace: "!default"
```
"""
        model = os.getenv("CODE_GEN_MODEL")
        api_key = os.getenv("CODE_GEN_API_KEY")
        print(f"Generating Kyverno policy code with '{model}'")
        print("Prompt:", prompt)
        answer = call_llm(prompt, model=model, api_key=api_key)
        code = extract_code(answer, code_type="yaml")
        policy_file = policy_file.strip('"').strip("'").lstrip("{").rstrip("}")
        if not policy_file:
            policy_file = "policy.yaml"
        fpath = os.path.join(self.workdir, policy_file)
        with open(fpath, "w") as f:
            f.write(code)
        print("Code in answer:", code)

        tool_output = f"""The generated policy is below:
```yaml
{code}
```

This policy file has been saved at {fpath}.
"""
        return tool_output


class RunKubectlToolInput(BaseModel):
    args: str = Field(
        description="command arguments after `kubectl`. `--kubeconfig` should be specified here. Multiple commands with `;` or `&&` is not allowed."
    )
    output_file: str = Field(description="The filepath to save the result. If empty string, not save anything", default="")
    return_output: str = Field(description='A boolean string. Set this to "True" if you want to get the command output', default="False")
    script_file: str = Field(description="A filepath. If provided, save the kubectl command as a script at the specified file.", default="")


class RunKubectlTool(BaseTool):
    name: str = "RunKubectlTool"
    # correct description
    description: str = """The tool to execute a kubectl command.
This tool returns the following:
  - return_code: if 0, the command was successful, otherwise, failure.
  - stdout: standard output of the command (only when `return_output` is True)
  - stderr: standard error of the command (only when error occurred)

For example, to execute `kubectl get pod -n default --kubeconfig kubeconfig.yaml`,
Tool Input should be the following:
{"args": "get pod -n default --kubeconfig kubeconfig.yaml", "output_file": "", "return_output": "True", "script_file": ""}

Hint:
- If you need to get all pods in all namespaces, you can do it by `kubectl get pods --all-namespaces --kubeconfig <kubeconfig_path> -o json`
"""
    args_schema: type[BaseModel] = RunKubectlToolInput

    # disable cache
    cache_function: Callable = lambda _args, _result: False

    workdir: str = ""
    read_only: bool = True

    def __init__(self, **kwargs):
        super_args = {k: v for k, v in kwargs.items() if k not in ["workdir", "read_only"]}
        super().__init__(**super_args)
        if "workdir" in kwargs:
            self.workdir = kwargs["workdir"]
        if "read_only" in kwargs:
            self.read_only = kwargs["read_only"]

    def _run(self, args: str, output_file: str, return_output: str = "False", script_file: str = "") -> str:
        print("RunKubectlTool is called")
        if "--kubeconfig" not in args:
            raise ValueError("--kubeconfig must be specified to avoid touching wrong cluster")

        if output_file and output_file.endswith(".json"):
            if "-o" not in args and "--output" not in args:
                args += " -o json"

        # remove if `kubectl` is included in the given args
        parts = args.strip().split(" ", 1)
        if len(parts) > 1 and "kubectl" in parts[0]:
            args = parts[1]

        if self.read_only:
            if not args.strip().startswith("get"):
                raise ValueError("Only `get` operation is allowed")

        cmd_str = f"kubectl {args}"
        print("[DEBUG] Running this command:", cmd_str)
        proc = subprocess.run(
            cmd_str,
            shell=True,
            cwd=self.workdir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        std_out = proc.stdout
        if len(std_out) > 1000:
            std_out = std_out[:1000] + "\n\n...Output is too long. Truncated here."

        std_err = proc.stderr
        if len(std_err) > 1000:
            std_err = std_err[:1000] + "\n\n...Output is too long. Truncated here."

        print("[DEBUG] kubectl result returncode:", proc.returncode)
        print("[DEBUG] kubectl result stdout:", std_out)
        print("[DEBUG] kubectl result stderr:", std_err)
        # if proc.returncode != 0:
        #     raise ValueError(f"failed to run a playbook; stdout: {proc.stdout}, stderr: {proc.stderr}")

        if output_file:
            opath = os.path.join(self.workdir, output_file)
            with open(opath, "w") as f:
                f.write(proc.stdout)

        return_output_bool = False
        if return_output:
            if isinstance(return_output, str):
                return_output_bool = return_output.lower() == "true"

        return_val = {"return_code": proc.returncode}
        if return_output_bool:
            return_val["stdout"] = std_out
        if proc.returncode != 0:
            return_val["stderr"] = std_err

        if script_file:
            cmd_str_ext = cmd_str
            actual_kubeconfig = os.path.join(self.workdir, "kubeconfig.yaml")
            cmd_str_ext = cmd_str_ext.replace("kubeconfig.yaml", actual_kubeconfig)
            if output_file:
                cmd_str_ext += f" > {output_file}"
            script_body = f"""#!/bin/bash
{cmd_str_ext}
"""
            spath = os.path.join(self.workdir, script_file)
            with open(spath, "w") as f:
                f.write(script_body)
            os.chmod(spath, 0o755)

        return return_val
