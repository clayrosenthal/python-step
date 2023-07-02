#!/usr/bin/env python3

from step.step_cli import StepCli
from step.models import *
import pytest
from typing import List



def test_step_help():
    """Tests the step help command."""
    step = StepCli()
    assert str(step.help) == "step help"
    

def test_step_ca_admin_list():
    """Tests the step ca admin list command."""
    step = StepCli()
    assert str(step.ca.admin.list) == "step ca admin list"
    output = step.ca.admin.list()
    assert isinstance(output, List)
    assert len(output) > 0 
    assert isinstance(output[0], StepAdmin)


    
