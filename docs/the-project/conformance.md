---
title: Conformance
description: The certification plans of the OpenID Foundation conformance suite that run against Beffroi, and what the mark means.
---

# Conformance

Loyalty is to the standard, not to a reading of the standard, so the protocol is judged from outside. The
conformance suite of the OpenID Foundation is open source, free to run, and it runs against the provider
in continuous integration.

## The plans that run

Each plan is a certification plan of the suite, played in `--strict`, the mode a certification submission
asks for: a warning there is a failure. Only the results a human must read on the plan's page, and the
ones the suite itself decides to skip, stay acceptable, because no run can avoid them.

| Family | Plans |
|---|---|
| OpenID Connect Core | Basic OP, Config OP, Form Post Basic OP |
| Logout | RP-Initiated Logout OP, Front-Channel Logout OP, Back-Channel Logout OP |
| FAPI 2.0 | Security DPoP, Security mTLS, Signing DPoP, Signing mTLS |
| FAPI-CIBA | Poll, Ping |
| Registration and bootstrap | Dynamic OP, Third Party-Init OP, Rotate Keys |

A module that stays red is listed with its reason and the issue that closes it, and the run then fails the
day it starts passing, so the line gets deleted rather than carried. The current state of every plan lives
in the code repository, beside the workflow that runs them, because that is where it is maintained.

## SAML 2.0

There is no certification programme for SAML 2.0, so the judges are the implementations the provider has to
work with, and tools that are not its own. Nothing the provider says of a signature it wrote counts as a proof
of that signature.

| Judge | What it plays | When |
|---|---|---|
| xmlsec1 and the OpenSSL command line | Every signature and every ciphertext the SAML packages write, under every algorithm the build supports, verified and decrypted; every signed HTTP-Redirect URL verified over the octets of the binding | In continuous integration, at every pull request |
| SimpleSAMLphp | A service provider of the identity provider, over both bindings, with an encrypted assertion and single logout started from either side; the upstream identity provider of the service provider, with a first sign-in, its groups and an encrypted assertion | By hand, against a running provider |
| Microsoft Entra ID | Federating its guests to the identity provider; the upstream identity provider of a tenant through an enterprise application | By hand, against a Microsoft tenant |
| Keycloak | The messages of the model and the bindings, both ways | By hand |

Besides those judges, the published corpora of attacks on XML signatures are part of the suites of the
packages, and every invariant of their specifications has its tests.

## What the mark means, and what it does not

!!! note "Beffroi is not OpenID Certified yet"

    Running the suite and being certified are two different things. The runs above are free and
    reproducible; the mark is a filing with the OpenID Foundation for a given deployment and a given major
    version. It will be announced here, with the entry in the public list, the day it is filed.

Certification qualifies the software. It says nothing about the organisation that operates a deployment,
which is what ISO 27001 and the national cloud qualifications are for. Those apply to a hosted service,
never to a bundle you install yourself.

## Running the suite yourself

The suite is a set of Docker images you can run locally against your own deployment, with no account and
no limit on the number of runs. The plans the project uses, and the task that drives them through the
suite's API, are in the code repository.
