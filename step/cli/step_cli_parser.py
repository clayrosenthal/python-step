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
import json
import logging
import string
import subprocess

ANSI_START = "[0;"
ANSI_BOLDER = "[0;1;99m"
ANSI_UNDERLINE = "[0;4;39m"
ANSI_ITALIC = "[0;3;39m"
ANSI_BOLD = "[0;1;39m"
ANSI_END = "[0m"
ANSI_SEQS = [ANSI_BOLDER, ANSI_UNDERLINE, ANSI_ITALIC, ANSI_BOLD, ANSI_END]


class StepCliParser:
    """A class to parse a single step command."""

    PARSER_VERSION: str = "0.1.1"
    __total_command_dict = None
    command_stack: list[str] = []
    log = logging.getLogger(__name__)
    command_dict: dict = {}
    command_output: list[str] = []
    command: str = ""
    i: int = -1
    line: str = ""
    arg_type: str = ""

    @classmethod
    def _ver_comp(cls, other: str) -> int:
        cur_ver = cls.PARSER_VERSION.split(".")
        other_ver = other.split(".")
        for i, ver_num in enumerate(cur_ver):
            if i >= len(other_ver) or ver_num > other_ver[i] or other_ver[i] == "":
                return 1
            elif ver_num < other_ver[i]:
                return -1
            else:
                continue
        return 0

    @staticmethod
    def _make_printable(s: str) -> str:
        return "".join(filter(lambda x: x in string.printable, s))

    @staticmethod
    def _remove_ansi_sequences(s: str) -> str:
        """Removes the ANSI escape sequences from a string.

        Args:
            s (str): The string to remove the sequences from.
        Returns:
            str: The string without the sequences.
        """
        for ansi in ANSI_SEQS:
            s = s.replace(ansi, "")
        return s

    @staticmethod
    def _arg_param_check(arg: str) -> tuple[str, str]:
        """Checks if the argument has a parameter.

        Args:
            arg (str): The argument.
        Returns:
            Tuple[str, str]: The argument and the parameter.
        """
        param = ""
        if "=" in arg:
            param = arg.split("=")[1]
            arg = arg.split("=")[0]
        return arg, param

    @staticmethod
    def _arg_form_check(arg: str) -> tuple[str, str]:
        """Checks if the argument has two forms.

        Args:
            arg (str): The argument.
        Returns:
            Tuple[str, str]: The first form and the second form.
        """
        alt_form = ""
        if "," in arg:
            alt_form = arg.split(",")[1].strip("- ").split("=")[0]
            arg = arg.split(",")[0]
        return arg, alt_form

    def __init__(self):
        # borg pattern
        if not StepCliParser.__total_command_dict:
            StepCliParser.__total_command_dict = self.command_dict
            self.command_dict["__subcommands__"] = {}
            self.command_dict["__arguments__"] = {}

        self.__total_command_dict = StepCliParser.__total_command_dict
        self.command_dict = self.__total_command_dict

    def _next_line(self):
        self.i += 1
        self.line = self.command_output[self.i]

    def _still_description(self) -> bool:
        if self.line != "":
            return True
        if self.i + 1 >= len(self.command_output):
            return False
        next_line = self.command_output[self.i + 1]
        if next_line.startswith(ANSI_BOLDER):
            return False
        next_line = next_line.strip(" ")
        if self.section == "options":
            rtn = not next_line.startswith(f"{ANSI_BOLDER}-")
        else:
            rtn = not next_line.startswith(ANSI_UNDERLINE)
        self.log.debug(f"next_line: `{next_line}`, still_description: {rtn}")
        return rtn

    def _get_description(self) -> str:
        """Gets the description of an option from the command output.

        Args:
            command_output (List[str]): The command output.
            i (int): The index of the option.
        Returns:
            str: The description of the option.
        """

        description = ""
        while self._still_description():
            self._next_line()
            description += self._remove_ansi_sequences(self.line).strip() + " "

        return description.strip(" ")

    def _parse_subcommand(self) -> tuple[str, str]:
        """Parses the subcommand from the command output.

        Returns:
            Tuple[str, str]: The parsed subcommand and the description.
        """
        subcommand = self._remove_ansi_sequences(self.line.split(ANSI_END)[0]).strip()
        alt_form = ""
        if "," in subcommand:
            alt_form = subcommand.split(",")[1].strip()
            subcommand = subcommand.split(",")[0]
        description = self._remove_ansi_sequences(self.line.split(ANSI_END)[1]).strip()

        self.log.debug(
            f"subcommand: {subcommand}{'/'+alt_form if alt_form else ''}, description: {description}"
        )
        return subcommand, description

    def _parse_command_parts(self) -> tuple[str, dict[str, str]]:
        """Parses the command arguments and options.

        Args:
            command_output (List[str]): The command output.
            i (int): The index of the option.
        Returns:
            Dict[str, str]: The parsed command arguments.
        """
        arg_dict = {}
        self.arg_type = self.section.rstrip("s")
        arg = self._remove_ansi_sequences(self.line).lstrip(" -")
        arg, alt_form = self._arg_form_check(arg)
        arg, param = self._arg_param_check(arg)
        arg_dict["description"] = self._get_description()
        if param:
            self.arg_type = "optional argument"
            arg_dict["param"] = param
        if alt_form:
            arg_dict["alt_form"] = alt_form
        arg_dict["type"] = self.arg_type
        self.log.debug(f"arg: {arg}, arg_dict: {arg_dict}")
        self.command_dict["__arguments__"][arg] = arg_dict
        if alt_form:
            arg_dict = arg_dict.copy()
            arg_dict["alt_form"] = arg
            self.command_dict["__arguments__"][alt_form] = arg_dict
        return arg, arg_dict

    def parse(self, command_stack: list[str]) -> dict[str, dict]:
        """Recursively parses the command to find the sub commands and options.

        Returns:
            Dict[str, Dict]: The parsed command.
        """
        if not command_stack or len(command_stack) <= 1 and command_stack[0] == "":
            return self.command_dict
        if command_stack[0] != "step":
            command_stack = ["step"] + command_stack
        self.command = command_stack[-1]
        if self.command in self.command_dict:
            self.command_dict = self.command_dict[self.command]
            return self.command_dict
        self.command_stack = command_stack
        if len(self.command_stack) == "1" and self.command_stack[0] == "step":
            return self.parse_loop()
        for part in self.command_stack[1:]:
            self.log.debug(f"part: {part}")
            if part not in self.command_dict:
                self.command_dict[part] = {"__subcommands__": {}, "__arguments__": {}}
            self.command_dict = self.command_dict[part]
            try:
                self.parse_loop()
            except Exception as e:
                self.log.error(
                    f"Error parsing {self.command}: {e}\n{self.command_dict}"
                )
                raise e

        return self.command_dict

    def parse_loop(self) -> dict[str, dict]:
        if not all(
            [
                str(key) in ["__subcommands__", "__arguments__"]
                for key in self.command_dict.keys()
            ]
        ):
            self.log.debug(f"pre-cached command_dict: {self.command_dict}")
            return self.command_dict

        self.section = "none"
        raw_command_output = subprocess.run(
            self.command_stack + ["--help"], shell=True, check=True, capture_output=True
        ).stdout
        self.command_output = self._make_printable(
            raw_command_output.decode("utf-8")
        ).split("\n")
        while self.i <= len(self.command_output):
            try:
                self._next_line()
            except IndexError:
                break
            if self.line.startswith(ANSI_BOLDER):
                self.section = self._remove_ansi_sequences(self.line).lower()
                self.log.debug(f"section: {self.section}")
                continue
            if self.section == "none":
                continue
            if self.section == "positional arguments" or self.section == "options":
                self._parse_command_parts()
                continue
            if self.section == "commands" and self.line:
                subcommand, description = self._parse_subcommand()
                self.command_dict["__subcommands__"][subcommand] = description
                continue
            if self.section == "version" and self.line:
                step_version = self.line[self.line.index("CLI/") + 4 :].strip()
                step_version = self._remove_ansi_sequences(step_version)
                self.command_dict["__cli_version__"] = step_version
                continue

        self.log.info(f"command_dict: {self.command_dict}")

        if self.command_dict["__subcommands__"] == {}:
            self.command_dict.pop("__subcommands__")
        if self.command_dict["__arguments__"] == {}:
            self.command_dict.pop("__arguments__")

        return self.command_dict


def main():
    json.dump(StepCliParser().parse(["step"]), open("step.json", "w"), indent=4)


if __name__ == "__main__":
    main()
