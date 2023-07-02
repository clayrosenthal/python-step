# Python class to run step cli commands nicely from python

import json
import shutil
import os
import subprocess
from typing import Any, Dict, List
import logging

from step.step_cli_parser import StepCliParser
from step.models import (
    StepAdmin,
    StepSshHost
)

STEP_JSON = os.environ.get("STEP_JSON", ".step-cli.json")

if shutil.which("step") is None:
    raise FileNotFoundError("step cli not found, refer to https://smallstep.com/docs/cli/ for installation instructions")
if os.path.isfile(STEP_JSON):
    with open(STEP_JSON, "r") as step_json:
        _command_dict = json.load(step_json)
        if StepCliParser._ver_comp(_command_dict.get("__version__", "0")) > 0:
            _command_dict = StepCliParser("step").parse(recurse=True, dump=STEP_JSON)
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
    
    def __str__(self) -> str:
        return self.command

    def __repr__(self) -> str:
        return f"StepCli: {self.command}, args: {self._global_args}"

    def add_args(self, **kwargs) -> None:
        self._global_args.update(kwargs)

    def _process_output(self, raw_output: str) -> Any:
        output = raw_output
        try:
            output = json.loads(raw_output)
        except:
            pass
        if "admin" in self.command:
            return [StepAdmin(l) for l in output.split("\n")[1:]]
        elif self.command == "step ssh hosts":
            return [StepSshHost(l) for l in output.split("\n")[1:]]
        elif self.command == "step context list":
            return [ (l.strip("▶ "), "▶" in l) for l in output.split("\n") ]
        elif self.command == "step ca health":
            return output == "ok"
        return output
    
    def __getattribute__(self, name: str) -> Any:
        """Gets the attribute of the StepCli class.
        
        Args:
            __name (str): The name of the attribute to get.
        
        Returns:
            Any: The attribute of the StepCli class.
        """
        if name in object.__getattribute__(self, "__dict__"):
            return object.__getattribute__(self, name)
        if name.lower() in self.command_dict.get("__subcommands__", {}):
            return StepCli(f"{self.command} {name.lower()}", **self._global_args)
        return object.__getattribute__(self, name)
    
    def __call__(self, *args: Any, _no_prompt=False, _raw_output=False, **kwargs: Any) -> Any:
        """Runs the command.
        
        Args:
            command (str): The command to run.
        """
        self.log.debug(f"global args: {self._global_args}")
        self.log.debug(f"args: {args}")
        self.log.debug(f"kwargs: {kwargs}")
        self.log.debug(f"command_dict: {self.command_dict}")
        command_to_run = self.command
        if args:
            command_to_run += " " + " ".join([str(r) for r in args])
        if kwargs:
            command_to_run += " " + self._make_args({**self._global_args, **kwargs})
        try:
            self.log.info(f"running command: {command_to_run}")
            _pipe = subprocess.DEVNULL if _no_prompt else None
            raw_output = subprocess.check_output(command_to_run, shell=True, stdin=_pipe, stderr=_pipe).decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            self.log.error(f"step return error: {e}")
            return None

        self.log.debug(f"raw_output: {raw_output}")
        return raw_output if _raw_output else self._process_output(raw_output)
    
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
        
def set_step_defaults(step: StepCli, **kwargs) -> None:
    step_path = step.path().strip()
    with open(f"{step_path}/config/defaults.json", "r") as defaults_file:
        defaults = json.load(defaults_file)
        defaults.update(kwargs)
        
    with open(f"{step_path}/config/defaults.json", "w") as defaults_file:
        json.dump(defaults, defaults_file, indent=4)

# step = StepCli()