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

## License
Licensed under GPLv3+, see [LICENSE](LICENSE) for full license text
Copyright by Clayton Rosenthal
