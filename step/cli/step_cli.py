#!/usr/bin/env python3
"""
Copyright (C) 2023 Clayton Rosenthal.

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

import argparse
import json
import logging
import os
import subprocess
from typing import Any

from step.cli.step_cli_parser import StepCliParser
from step.models import StepAdmin, StepCertificate, StepSshHost, StepVersion

STEP_JSON = os.environ.get("STEP_JSON", ".step-cli.json")


def parse_args():
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run step cli commands with python wrapper."
    )
    parser.add_argument("-c", "--command", help="The command to run.", required=True)
    parser.add_argument(
        "-a", "--args", help="The args to pass to the command.", nargs="*"
    )
    parser.add_argument("-r", "--raw", help="Print raw output.", action="store_true")
    parser.add_argument(
        "-s", "--stdin", help="Don't pass stdin to command.", action="store_true"
    )
    parser.add_argument(
        "-e", "--stderr", help="Don't pass stderr to command.", action="store_true"
    )
    parser.add_argument("-v", "--verbose", help="Verbose output.", action="store_true")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    command = args.command
    command_args = args.args
    raw = args.raw
    stdin = args.stdin
    stderr = args.stderr
    verbose = args.verbose
    log = logging.getLogger(__name__)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        log.debug("command: %s", command)
        log.debug("command_args: %s", command_args)
        log.debug("raw: %s", raw)
        log.debug("stdin: %s", stdin)
        log.debug("stderr: %s", stderr)

    step = StepCli()
    for part in command.split(" "):
        step = getattr(step, part)

    arg_dict = {}
    if command_args:
        arg_dict = {a.split("=")[0]: a.split("=")[1] for a in command_args}

    output = step(**arg_dict, _raw_output=raw, _no_stdin=stdin, _no_stderr=stderr)
    if output:
        print(f"cmd `{command}`: {output}")


class StepArgs:
    positional: list[str]
    named: dict[str, str]
    command: str
    possible_args: dict[str, str] = {}
    arg_list: list[str] = []

    def __init__(
        self,
        command: str,
        positional: list[str],
        named: dict[str, Any],
        possible_args: dict[str, Any],
    ) -> None:
        self.command = command
        self.positional = positional
        self.named = named
        self.possible_args = possible_args
        self.arg_list = [str(a) for a in self.positional]
        for key, value in self.named.items():
            if key.startswith("_"):
                continue
            else:
                key = key.replace("_", "-")
            if key not in self.possible_args:
                raise ValueError(
                    f"argument '{key}' not found in command '{self.command}'"
                )
            if value is True:
                self.arg_list += [f"'--{key}'"]
            elif isinstance(value, list):
                for v in value:
                    self.arg_list += [f"'--{key}={v}'"]
            else:
                self.arg_list += [f"'--{key}={value}'"]

    def __repr__(self) -> str:
        return (
            f"StepArgs(command={self.command}, positional={self.positional}, "
            + f"named={self.named}, possible_args={self.possible_args})"
        )

    def __str__(self) -> str:
        return " ".join(self.arg_list)


class StepCli:
    """Class to run step cli commands nicely from python."""

    _command_stack: list[str] = []  # the stack of parts of the command to run
    # _cli_dict: dict[str, Any] = {}
    _command: str = ""  # the command the class is representing
    _command_dict: dict = {}  # the parsed command, subcommands, arguements, etc.
    _log: logging.Logger = logging.getLogger(__name__)
    _global_args = {}  # global args to pass to the command

    def __init__(self) -> None:
        """Initializes the StepCli class."""
        # self._cli_dict = {}
        self._command = "step"
        self._command_stack = ["step"]
        self._command_dict = {}
        self._log = logging.getLogger(__name__)
        self._global_args = {}
        self._command_dict = StepCliParser().parse(["step"])

    def _set_command(
        self,
    ) -> None:  # , next_step: str, global_args: dict | None = None) -> None:
        """Makes the command to run."""
        self._command = " ".join(self._command_stack)
        self._log.debug(f"command: {self._command}")
        self._command_dict = StepCliParser().parse(self._command_stack)
        # if global_args:
        #     self._log.debug(f"global args passed: {global_args}")
        #     self._global_args = global_args

    def __str__(self) -> str:
        return self._command

    def __repr__(self) -> str:
        return f"StepCli: {self._command}, args: {self._global_args}"

    def _add_args(self, **kwargs) -> None:
        self._global_args.update(kwargs)

    def _process_output(self, raw_output: str, command_ran: str) -> Any:
        output = raw_output
        if "admin" in self._command:
            return [StepAdmin(l) for l in output.split("\n")[1:]]
        elif self._command == "step ssh hosts":
            return [StepSshHost(l) for l in output.split("\n")[1:]]
        elif self._command == "step context list":
            return [(l.strip("▶ "), "▶" in l) for l in output.split("\n")]
        elif self._command == "step ca health":
            return output == "ok"
        elif self._command == "step version":
            return StepVersion(output)
        elif self._command == "step ca certificate":
            cert_path = command_ran.split(" ")[4].strip()
            return StepCertificate(cert_path)
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
        if name == "__dict__":
            return object.__getattribute__(self, name)
        # logging.getLogger(__name__).debug(
        #         f"obj dict: {object.__getattribute__(self, '__dict__')}"
        #     )
        try:
            if name in object.__getattribute__(self, "__dict__"):
                return object.__getattribute__(self, name)
            next_part = name.lower()
            # self._command_stack.append(next_part)
            # self._set_command()
            # self._command = " ".join(self._command_stack)
            # self._command_dict = StepCliParser().parse(self._command_stack)
            match next_part:
                case "_command":
                    default_get = "step"
                case "_command_stack":
                    default_get = []
                case "_command_dict":
                    default_get = {}
                case _:
                    default_get = ""
            # return object.__getattribute__(self, '__dict__').get(next_part, default_get)
            # if next_part not in self._cli_dict and next_part in self._command_dict.get(
            #     "__subcommands__", {}
            # ):
            #     # TODO: make crazy singleton to avoid this
            #     self._cli_dict[next_part] = StepCli()._make_command(
            #         self._command_stack + [next_part], self._global_args
            #     )
            # if next_part in self._cli_dict:
            #     return self._cli_dict[next_part]
            return object.__getattribute__(self, name)
        except AttributeError:
            logging.getLogger(__name__).debug(
                f"obj dict: {object.__getattribute__(self, '__dict__')}"
            )
            if not self._command_dict:
                self._command_dict = {}
            if not self._command_stack:
                self._command_stack = ["step"]
            else:
                raise AttributeError(f"StepCli object has no attribute {name}")
        finally:
            if self._command_stack:
                self._command_stack.pop()
                self._set_command()

    def __call__(
        self,
        *args: Any,
        _no_stdin=False,
        _no_stderr=False,
        _raw_output=False,
        **kwargs: Any,
    ) -> Any:
        """Runs the command.

        Args:
            command (str): The command to run.
        """
        self._log.debug(f"global args: {self._global_args}")
        self._log.debug(f"args: {args}")
        self._log.debug(f"kwargs: {kwargs}")
        self._log.debug(f"command_dict: {self._command_dict}")
        command_to_run = self._command
        named_args = {**self._global_args, **kwargs}
        command_to_run += f" {StepArgs(self._command, [str(r) for r in args], named_args, self._command_dict.get('__arguments__', {}))}"
        try:
            self._log.debug(f"running command: {command_to_run}")
            _stdin = subprocess.DEVNULL if _no_stdin else None
            _stderr = subprocess.DEVNULL if _no_stderr else None
            process_result = subprocess.run(
                command_to_run,
                shell=True,
                check=True,
                stdin=_stdin,
                stderr=_stderr,
                stdout=subprocess.PIPE,
            )
            _raw_output = process_result.stdout.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            self._log.error(f"step return error: {e}")
            return None

        self._log.debug(f"raw_output: `{_raw_output}`")
        return (
            _raw_output
            if _raw_output
            else self._process_output(_raw_output, command_to_run)
        )

    @property
    def _step_path(self) -> str:
        """Gets the step path.

        Returns:
            str: The step path.
        """
        prev_command = self._command
        if self._command != "step":
            self._command = "step"
        # only works if called from a step command, so save old command if not
        step_path = self.path()
        self._command = prev_command
        return step_path

    def _add_step_defaults(self, **kwargs) -> None:
        """Adds arguments to the step defaults config file."""
        if not kwargs:
            return

        new_args = kwargs.keys()
        defaults = {}

        with open(f"{self._step_path}/config/defaults.json") as defaults_file:
            defaults = json.load(defaults_file)
            defaults.update({str(k).replace("-", "_"): kwargs[k] for k in new_args})

        with open(f"{self._step_path}/config/defaults.json", "w") as defaults_file:
            json.dump(defaults, defaults_file, indent=4)
