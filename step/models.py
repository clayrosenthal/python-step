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

from typing import List
from datetime import datetime

class StepVersion:
    version: str
    platform: str
    release: datetime

    def __init__(self, output: str) -> None:
        self.version = output[output.index("CLI/")+4:].split()[0]
        self.platform = output[output.index("(")+1:output.index(")")]
        self.release = datetime.fromisoformat(output[output.index(":")+2:].replace(' UTC','Z').replace(' ','T'))
    
    def __repr__(self) -> str:
        return (
            f"version: {self.version}, " +
            f"platform: {self.platform}, " + 
            f"release: {self.release.isoformat()}"
        )

class StepAdmin:
    subject: str
    provisioner: str
    super_admin: bool

    def __init__(self, line: str) -> None:
        self.subject = line.split()[0].strip()
        self.provisioner = line[len(self.subject):line.index(")")+1].strip()
        self.super_admin = bool('SUPER' in line[line.index(")")+1:])


    def __repr__(self) -> str:
        return (
            f"subject: {self.subject}, " +
            f"provisioner: {self.provisioner}, " + 
            f"type: {'SUPER_ADMIN' if self.super_admin else 'ADMIN'}"
        )
    
    def __str__(self) -> str:
        return (
            f"subject: {self.subject}, " +
            f"provisioner: {self.provisioner}, " + 
            f"type: {'SUPER_ADMIN' if self.super_admin else 'ADMIN'}"
        )

class StepSshHost:
    hostname: str
    host_id: int = 0
    tags: List[str] = []

    def __init__(self, line: str) -> None:
        self.hostname = line.split(" ")[0].strip()
        if len(self.hostname) == len(line.strip()):
            return
        host_id_str = line[len(self.hostname):].split()[0].strip()
        self.host_id = int(host_id_str) if host_id_str.isdigit() else 0
        self.tags = line[line.index(host_id_str):].split()
    
    def __repr__(self) -> str:
        return (
            f"hostname: {self.hostname}" +
            (f", id: {self.host_id}" if self.host_id else '') + 
            (f", tags: {', '.join(self.tags)}" if self.tags else '')
        )
    
    def __str__(self) -> str:
        return (
            f"hostname: {self.hostname}" +
            (f", id: {self.host_id}" if self.host_id else '') + 
            (f", tags: {', '.join(self.tags)}" if self.tags else '')
        )