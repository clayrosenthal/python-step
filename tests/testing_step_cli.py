#!/usr/bin/env python3

from step.step_cli import StepCli
from step.models import *
# import pytest
from typing import List



def test_step_help():
    """Tests the step help command."""
    step = StepCli()
    assert str(step.help) == "step help"

def test_step_ca_health():
    """Tests the step ca health command."""
    step = StepCli()
    test = step.ca.health
    assert str(test) == "step ca health"
    output = test()
    assert isinstance(output, bool)
    assert output is True

def test_step_ca_health_raw():
    """Tests the step ca health command with raw output."""
    step = StepCli()
    test = step.ca.health
    assert str(test) == "step ca health"
    output = test(_raw_output=True)
    assert isinstance(output, str)
    assert output == "ok"
    
def test_step_ca_admin_list():
    """Tests the step ca admin list command."""
    step = StepCli()
    assert str(step.ca.admin.list) == "step ca admin list"
    output = step.ca.admin.list()
    assert isinstance(output, List)
    assert len(output) > 0 
    assert isinstance(output[0], StepAdmin)


def test_step_ssh_hosts():
    """Tests the step ssh hosts command."""
    step = StepCli()
    assert str(step.ssh.hosts) == "step ssh hosts"
    output = step.ssh.hosts()
    assert isinstance(output, List)
    assert len(output) > 0
    assert isinstance(output[0], StepSshHost)

def test_step_version():
    """Tests the step version command."""
    step = StepCli()
    assert str(step.version) == "step version"
    output = step.version()
    assert isinstance(output, StepVersion)
    assert output.version == "0.24.4"

def test_step_version_raw():
    """Tests the step version command with raw output."""
    step = StepCli()
    assert str(step.version) == "step version"
    output = step.version(_raw_output=True)
    assert isinstance(output, str)
    assert output == """Smallstep CLI/0.24.4 (darwin/arm64)
Release Date: 2023-05-12 00:33 UTC"""