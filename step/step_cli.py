# Python class to run step cli commands nicely from python

import json
import shutil
import os
import subprocess
from typing import Any, Dict, List
import logging

from step.step_cli_parser import StepCliParser

STEP_JSON = os.environ.get("STEP_JSON", ".step-cli.json")

if shutil.which("step") is None:
    raise FileNotFoundError("step cli not found, refer to https://smallstep.com/docs/cli/ for installation instructions")
if os.path.isfile(STEP_JSON):
    _command_dict = json.load(open(STEP_JSON, "r"))
else:
    _command_dict = StepCliParser("step").parse(recurse=True, dump=STEP_JSON)

class StepCli:
    """Class to run step cli commands nicely from python."""
    command: str = ""
    log: logging.Logger = logging.getLogger(__name__)
    _global_args = {}

    def __init__(self, command: str = "step", **kwargs) -> None:
        """Initializes the StepCli class."""
        if not command.startswith("step"):
            command = f"step {command}"
        self.command = command
        self.log = logging.getLogger(__name__)
        self.log.debug(f"command: {command}")
        command_list = command.split(" ")
        # step itself isn't in dict, is the top level
        self.command_dict = _command_dict 
        for part in command_list[1:]:
            self.log.debug(f"part: {part}")
            self.command_dict = self.command_dict.get(part, {})
        
        if kwargs:
            self.log.debug(f"global args passed: {kwargs}")
            self._global_args = kwargs
    

    def add_args(self, **kwargs) -> None:
        self._global_args.update(kwargs)
        
    
    def __getattribute__(self, name: str) -> Any:
        """Gets the attribute of the StepCli class.
        
        Args:
            __name (str): The name of the attribute to get.
        
        Returns:
            Any: The attribute of the StepCli class.
        """
        if name in object.__getattribute__(self, "__dict__"):
            return object.__getattribute__(self, name)
        if name in self.command_dict.get("__subcommands__", {}):
            return StepCli(f"{self.command} {name}")
        return object.__getattribute__(self, name)
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Runs the command.
        
        Args:
            command (str): The command to run.
        """
        self.log.debug(f"running command: {self.command}")
        self.log.debug(f"args: {args}")
        self.log.debug(f"kwargs: {kwargs}")
        self.log.debug(f"command_dict: {self.command_dict}")
        command_to_run = self.command
        if args:
            command_to_run += " " + " ".join([str(r) for r in args])
        if kwargs:
            command_to_run += " " + self._make_args(kwargs)
        try:
            raw_output = subprocess.check_output(command_to_run, shell=True).decode("utf-8")
        except subprocess.CalledProcessError as e:
            self.log.error(f"step return error: {e}")
            return None

        self.log.debug(f"raw_output: {raw_output}")
        return raw_output
    
    def _make_args(self, args: Dict[str, Any]) -> str:
        """Makes the arguments string.
        
        Args:
            args (Dict[str, Any]): The arguments to make.
        
        Returns:
            str: The arguments string.
        """
        rtn = ""
        for key, value in args.items():
            if value is True:
                rtn += f" '--{key}'"
            elif isinstance(value, List):
                for v in value:
                    rtn += f" '--{key}={v}'"
            else:
                rtn += f" '--{key}={value}'"
        return rtn.strip(" ")
        

# step = StepCli()