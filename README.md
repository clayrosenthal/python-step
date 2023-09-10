# python-step
Python interface to [smallstep cli](https://smallstep.com/docs/step-cli/) api,
and [smallstep ca](https://smallstep.com/docs/step-ca/) api.

Currently is basically just a wrapper to the cli, with a bit of output parsing.
The end goal is replicating all the functionality of step-cli within python itself.

## Current Features:
 - Replication of step cli tool as python object
 - Some types of parsed output

## Planned Features:
 - Client CA Bootstrapping
 - SSH logging in
 - SSH Host setup
 - x509 User/host certs
 - CA initialization
 - CA management (provisioners, policy, etc)


## Usage
The current wrapper is defined as the StepCli class. You can use it as if
you are using the step-cli, but with `.`'s instead of spaces, and passing the
parameters to the call, replacing `-`'s with `_`'s.
```
from step import StepCli
step = StepCli()
step.ca.bootstrap(ca_url="ca.example.com", fingerprint="FINGERPRINTOFYOURCA")
step.ssh.login(provisioner="OIDC")
```

## License
Licensed under GPLv3+, see [LICENSE](LICENSE) for full license text
Copyright by Clayton Rosenthal
