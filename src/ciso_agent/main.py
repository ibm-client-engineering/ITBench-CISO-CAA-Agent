# Copyright contributors to the ITBench project. All rights reserved.
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
from ciso_agent.manager import CISOManager, CISOState
from typing import Optional


def run(inputs: dict) -> dict:
    """
    Runs the CISO agent with the provided input state.

    Args:
        inputs (dict): Dictionary representing the CISOState.

    Returns:
        dict: The result returned by the agent after invocation.
    """
    manager = CISOManager(eval_policy=False)
    return manager.invoke(inputs)

def main(goal: str = "", output: Optional[str] = None) -> None:
    """
    Main entry point for running the agent with a simple goal string.

    Args:
        goal (str): The compliance goal for the agent to achieve.
    """
    inputs = CISOState(goal=goal)
    result = run(inputs=inputs)
    result_json_str = json.dumps(result, indent=2)
    if output:
        with open(output, "w") as f:
            f.write(result_json_str)
        print("Output saved to ", output)
    else:
        print(result_json_str)

if __name__ == "__main__":
    main()