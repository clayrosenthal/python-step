
from typing import List


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