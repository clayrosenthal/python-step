#!/usr/bin/env python3

import logging

from test_params import *

from step import *

# import pytest


log = logging.getLogger("test-step-cli")


def test_step_cli():
    """Tests the StepCli class."""
    log.debug("start testing")
    step = StepCli()
    assert isinstance(step, StepCli)
    assert str(step) == "step"


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
    assert (
        output
        == """Smallstep CLI/0.24.4 (darwin/arm64)
Release Date: 2023-05-12 00:33 UTC"""
    )


def test_step_help():
    """Tests the step help command."""
    step = StepCli()
    assert str(step.help) == "step help"


def test_step_path():
    """Tests the step path command."""
    step = StepCli()
    assert str(step.path) == "step path"
    output = step.path()
    assert isinstance(output, str)
    # assumes the user is running this test on a mac
    assert output.startswith(f"/Users/{USER}/.step")


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


def test_step_ca_certificate():
    """Tests the step ca certificate command."""
    step = StepCli()
    step_path = step.path()
    test = step.ca.certificate
    assert str(test) == "step ca certificate"
    output = test(
        f"{USER}@{DOMAIN}",
        f"{step_path}/certs/{USER}.crt",
        f"{step_path}/secrets/{USER}.key",
        provisioner=STEP_PROVISIONER,
    )
    assert isinstance(output, StepCertificate)
    # assert output.subject == f"{USER}@{DOMAIN}"
    assert output.cert == f"/Users/{USER}/.step/certs/{USER}.crt"
    # assert output.key == f"/Users/{USER}/.step/secrets/{USER}.key"
    # assert output.provisioner == STEP_PROVISIONER


def test_step_ca_admin_list():
    """Tests the step ca admin list command."""
    step = StepCli()
    assert str(step.ca.admin.list) == "step ca admin list"
    output = step.ca.admin.list()
    assert isinstance(output, list)
    assert len(output) > 0
    assert isinstance(output[0], StepAdmin)


def test_step_ssh_hosts():
    """Tests the step ssh hosts command."""
    step = StepCli()
    assert str(step.ssh.hosts) == "step ssh hosts"
    output = step.ssh.hosts()
    assert isinstance(output, list)
    assert len(output) > 0
    assert isinstance(output[0], StepSshHost)


if __name__ == "__main__":
    test_step_cli()
    test_step_version()
