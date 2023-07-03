"""
Copyright (C) 2023 Clayton Rosenthal

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
import shutil
import os
import subprocess
from typing import Any, Dict, List
import logging

from step.step_cli_parser import StepCliParser
from step.models import *

STEP_JSON = os.environ.get("STEP_JSON", ".step-cli.json")

if shutil.which("step") is None:
    raise FileNotFoundError("step cli not found, refer to https://smallstep.com/docs/cli/ for installation instructions")
if os.path.isfile(STEP_JSON):
    with open(STEP_JSON, "r") as step_json:
        _base_command_dict = json.load(step_json)
        if StepCliParser._ver_comp(_base_command_dict.get("__version__", "0")) > 0:
            _base_command_dict = StepCliParser("step").parse(recurse=True, dump=STEP_JSON)
else:
    _base_command_dict = StepCliParser("step").parse(recurse=True, dump=STEP_JSON)

class StepCli:
    """Class to run step cli commands nicely from python."""
    _command: str = "" # the command the class is representing
    _command_dict: Dict = {} # the parsed command, subcommands, arguements, etc.
    _cached: bool = True # whether to use the cached version of the parsed command
    _log: logging.Logger = logging.getLogger(__name__)
    _global_args = {} # global args to pass to the command

    def __init__(self, _command: str = "step", _cached=True, **kwargs) -> None:
        """Initializes the StepCli class."""
        if not _command.startswith("step"):
            _command = f"step {_command}"
        self._command = _command
        self._cached = _cached
        self._log = logging.getLogger(__name__)
        self._log.debug(f"command: {_command}")
        if kwargs:
            self._log.debug(f"global args passed: {kwargs}")
            self._global_args = kwargs

        if not _cached:
            self._command_dict = StepCliParser(command=_command).parse()
            return
        # step itself isn't in dict, is the top level
        self._command_dict = _base_command_dict 
        command_list = _command.split(" ")
        for part in command_list[1:]:
            self._log.debug(f"part: {part}")
            self._command_dict = self._command_dict.get(part, {})
        

    
    def __str__(self) -> str:
        return self._command

    def __repr__(self) -> str:
        return f"StepCli: {self._command}, args: {self._global_args}"

    def _add_args(self, **kwargs) -> None:
        self._global_args.update(kwargs)

    def _process_output(self, raw_output: str) -> Any:
        output = raw_output
        if "admin" in self._command:
            return [StepAdmin(l) for l in output.split("\n")[1:]]
        elif self._command == "step ssh hosts":
            return [StepSshHost(l) for l in output.split("\n")[1:]]
        elif self._command == "step context list":
            return [ (l.strip("▶ "), "▶" in l) for l in output.split("\n") ]
        elif self._command == "step ca health":
            return output == "ok"
        elif self._command == "step version":
            return StepVersion(output)
        try:
            output = json.loads(raw_output)
        except:
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
        if name.lower() in self._command_dict.get("__subcommands__", {}):
            return StepCli(f"{self._command} {name.lower()}", _cached=self._cached, **self._global_args)
        return object.__getattribute__(self, name)
    
    def __call__(self, *args: Any, _no_prompt=False, _raw_output=False, **kwargs: Any) -> Any:
        """Runs the command.
        
        Args:
            command (str): The command to run.
        """
        self._log.debug(f"global args: {self._global_args}")
        self._log.debug(f"args: {args}")
        self._log.debug(f"kwargs: {kwargs}")
        self._log.debug(f"command_dict: {self._command_dict}")
        command_to_run = self._command
        if args:
            command_to_run += " " + " ".join([str(r) for r in args])
        if kwargs:
            command_to_run += " " + self._make_args({**self._global_args, **kwargs})
        try:
            self._log.debug(f"running command: {command_to_run}")
            _pipe = subprocess.DEVNULL if _no_prompt else None
            raw_output = subprocess.check_output(command_to_run, shell=True, stdin=_pipe, stderr=_pipe).decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            self._log.error(f"step return error: {e}")
            return None

        self._log.debug(f"raw_output: {raw_output}")
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
            if key.startswith("_"):
                continue
            if key not in self._command_dict.get("__arguments__", {}):
                raise ValueError(f"argument '{key}' not found in command '{self._command}'")
            if value is True:
                rtn += f" '--{key}'"
            elif isinstance(value, List):
                for v in value:
                    rtn += f" '--{key}={v}'"
            else:
                rtn += f" '--{key}={value}'"
        return rtn.strip(" ")
        
    def _add_step_defaults(self, **kwargs) -> None:
        """Adds arguments to the step defaults config file."""
        if not kwargs:
            return
        prev_command = self._command
        if self._command != "step":
            self._command = "step"
        # only works if called from a step command, so save old command if not
        step_path = self.path() 
        self._command = prev_command
        with open(f"{step_path}/config/defaults.json", "r") as defaults_file:
            defaults = json.load(defaults_file)
            defaults.update(kwargs)
            
        with open(f"{step_path}/config/defaults.json", "w") as defaults_file:
            json.dump(defaults, defaults_file, indent=4)