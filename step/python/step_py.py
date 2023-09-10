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

import os

import requests
from cryptography import x509
from cryptography.x509 import Certificate


def _path(path_str: str) -> str:
    if not path_str:
        return ""
    path_list = path_str.split("/")
    if path_list[0].startswith("~"):
        path_list[0] = os.path.expanduser(path_list[0])
        print(f"expanded path: {path_list[0]}")
    rtn = os.path.join(*path_list)
    rtn = os.path.normpath(rtn)
    print(f"resolved path: {rtn}")
    return rtn


def _mkdir(path_str: str) -> None:
    if not os.path.isdir(_path(path_str)):
        os.mkdir(_path(path_str))


class StepContext:
    ca_url: str = ""  # URL of step-ca instance
    fingerprint: str = ""  # Fingerprint of step-ca instance
    context: str = ""  # Context Name of step-ca instance
    authority: str = ""  # Authority Name of step-ca instance
    profile: str = ""  # Profile Name of step-ca instance
    version: str = ""  # Version of step-ca instance
    step_path: str = ""  # Path locally to files for step
    root_cert_path: str = ""  # Path locally to certificate of step-ca instance
    root_certs: list[Certificate] = []  # Root certificates of step-ca instance

    def __init__(
        self,
        ca_url: str,
        fingerprint: str,
        context: str = "",
        authority: str = "",
        profile: str = "",
    ) -> None:
        self.ca_url = ca_url if ca_url.startswith("https://") else f"https://{ca_url}"
        self.fingerprint = fingerprint
        self.context = context
        self.authority = authority
        self.profile = profile
        self._resolve_step_path()
        self._init_step_path()
        self._get_version()
        self._get_root_certs()

    @property
    def path(self) -> str:
        """Get the path to the step files."""
        return self.step_path

    def _resolve_step_path(self) -> None:
        """Resolves the path to the step files."""
        if os.environ.get("STEPPATH"):
            self.step_path = os.environ.get("STEPPATH", "")
            return
        elif os.path.isdir(_path("~/.step")):
            self.step_path = _path("~/.step")
            return
        elif os.path.isdir(_path("/usr/local/etc/step")):
            self.step_path = _path("/usr/local/etc/step")
            return
        elif os.path.isdir(_path("/etc/step")):
            self.step_path = _path("/etc/step")
            return
        else:
            self.step_path = _path("~/.step")

    def _init_step_path(self) -> None:
        _mkdir(self.step_path)
        [_mkdir(f"{self.step_path}/{path}") for path in ["certs", "ssh", "config"]]

    def _get_version(self) -> None:
        """Get the version of the step-ca instance."""
        response = requests.get(f"{self.ca_url}/version", verify=False)
        self.version = response.json().get("version", "")

    def _get_root_certs(self) -> None:
        """Get the root certificates of the step-ca instance."""
        response = requests.get(f"{self.ca_url}/root/{self.fingerprint}", verify=False)
        self.root_cert_path = _path(f"{self.path}/certs/root_ca.crt")
        with open(self.root_cert_path, "wb") as f:
            self.root_certs = list(x509.load_pem_x509_certificate(response.content))
            [
                f.write(root_cert.public_bytes(encoding=x509.Encoding.PEM))
                for root_cert in self.root_certs
            ]


class StepPy:
    """Class for interacting with a step-ca instance through python."""

    context: StepContext | None = None

    def bootstrap(self, ca_url: str, fingerprint: str) -> None:
        """Bootstrap a connection to step-ca instance."""
        self.context = StepContext(ca_url, fingerprint)
        self.ca_url = ca_url
        self.fingerprint = fingerprint
        self._get_version()
        self._get_root_certs()


# apis to implement
API_TODO = """
    r.MethodFunc("GET", "/version", Version)
    r.MethodFunc("GET", "/health", Health)
    r.MethodFunc("GET", "/root/{sha}", Root)
    r.MethodFunc("POST", "/sign", Sign)
    r.MethodFunc("POST", "/renew", Renew)
    r.MethodFunc("POST", "/rekey", Rekey)
    r.MethodFunc("POST", "/revoke", Revoke)
    r.MethodFunc("GET", "/crl", CRL)
    r.MethodFunc("GET", "/provisioners", Provisioners)
    r.MethodFunc("GET", "/provisioners/{kid}/encrypted-key", ProvisionerKey)
    r.MethodFunc("GET", "/roots", Roots)
    r.MethodFunc("GET", "/roots.pem", RootsPEM)
    r.MethodFunc("GET", "/federation", Federation)
    // SSH CA
    r.MethodFunc("POST", "/ssh/sign", SSHSign)
    r.MethodFunc("POST", "/ssh/renew", SSHRenew)
    r.MethodFunc("POST", "/ssh/revoke", SSHRevoke)
    r.MethodFunc("POST", "/ssh/rekey", SSHRekey)
    r.MethodFunc("GET", "/ssh/roots", SSHRoots)
    r.MethodFunc("GET", "/ssh/federation", SSHFederation)
    r.MethodFunc("POST", "/ssh/config", SSHConfig)
    r.MethodFunc("POST", "/ssh/config/{type}", SSHConfig)
    r.MethodFunc("POST", "/ssh/check-host", SSHCheckHost)
    r.MethodFunc("GET", "/ssh/hosts", SSHGetHosts)
    r.MethodFunc("POST", "/ssh/bastion", SSHBastion)
"""
