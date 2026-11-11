# Threat model

Reforge may inspect and execute untrusted third-party repositories. Treat source
code, build hooks, tests, package metadata and generated artifacts as hostile.

## Verification boundary

The Docker runner disables networking, drops access to the host repository by
mounting it read-only, runs as an unprivileged image user, uses a read-only root
filesystem, and enforces memory, CPU, process and wall-clock limits. It copies
the source into a temporary container filesystem before running project code.
Do not mount credentials, Docker sockets, SSH agents, or host home directories.

## Limits

Container isolation reduces exposure; it is not a proof of safety against kernel
or container-runtime vulnerabilities. Use a disposable host or stronger VM
boundary for highly adversarial repositories. The runner collects coverage and
enforces a configurable diff-size policy, but these guards only constrain known
failure modes. Model output is untrusted and must be reviewed and verified
before acceptance.
