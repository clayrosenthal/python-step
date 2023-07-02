#!/usr/bin/env python3

from step.step_cli import StepCli
import pytest



@pytest
def test_step_help():
    """Tests the step help command."""
    step = StepCli()
    step.help()
    assert step.help == "step help"

def test_step_ca_admin_list()
    """Tests the step ca admin list command."""
    step = StepCli()
    step.ca.admin.list()
    assert step.ca.admin.list == "step ca admin list"
