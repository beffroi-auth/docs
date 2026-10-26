---
title: The tenant and its keys
description: Writing the row of the tenant, generating a signing key, and checking that the key management service can open it.
---

# The tenant and its keys

A provider that cannot sign cannot answer. Two things happen before the first request: the tenant of the
configuration gets its row, and it gets a key.

## The schema

The bundle ships its Doctrine migrations, and registers their path with `doctrine/doctrine-migrations-bundle`
when the application has it, which provides the command:

``` bash
bin/console doctrine:migrations:migrate
```

## The tenant

The tenant is declared in the configuration, not created by a command: the issuer is a property of the
deployment. The command writes the row that matches what the configuration says.

``` bash
bin/console beffroi:tenant:synchronize
```

It writes what the configuration says of the tenant, its name, its look, the claims its people may change of
themselves and the classes it answers with, and prints the tenant it synchronised. Run it on every
deployment. The issuer is the one thing it never changes: every token a tenant issued names it, so a
configuration that gives a tenant another issuer is refused, by this command and by the provider, which
serves nothing while its row and its configuration disagree. Another issuer is another tenant, under another
slug.

## Its first keys

``` bash
bin/console beffroi:keys:generate --algorithm=MESSAGE-SEAL
bin/console beffroi:keys:generate
bin/console beffroi:keys:list
```

**The key the messages are sealed to comes first.** Nothing the provider writes to a transport leaves the
process in clear, and drawing any other key announces its own staging on a transport: on a tenant that does
not hold a `MESSAGE-SEAL` key yet, that announcement has nothing to be sealed to, and the command fails. Then
comes the signing key of the default algorithm, and then a key for each further algorithm the deployment
serves, `SAML-SIGNING` among them for a tenant that speaks SAML.

`beffroi:keys:generate` draws a key, seals it with the configured key management service and makes it the
active key of its algorithm at once. That is the right command for an empty deployment and the wrong one
for a live deployment, where [`beffroi:keys:rotate`](../reference/console-commands.md) replaces a key
without an outage: it stages the new key, publishes it in the JWK Set immediately, and lets it take over
once the staging delay has elapsed, so a client that cached the key set still verifies what it receives.

Check that the keys in use can actually be opened:

``` bash
bin/console beffroi:keys:list --check
```

That opens the keys in use, and the ones about to be, with the key management service, and fails on one it
cannot open or one that has worked past its age with nothing staged behind it. It is worth running in a
deployment pipeline: a key the provider cannot open is an outage at the first token request, not at the
next rotation.

A key works for an age, ninety days unless the configuration says otherwise, counted from the moment it
became active, and a year for the SAML signing key, whose family has figures of its own. Reaching it is not
an outage either: a timed step stages a successor without anybody asking for one. That is what `--check`
reports of an active key, in one of three answers: it has not worked past its age, it has and a successor is
staged behind it, or it has and nothing is staged. The last one fails the run, because a planning that has
stopped looks exactly like that from outside.

## A user

``` bash
bin/console beffroi:user:create alice --email alice@example.com
bin/console beffroi:user:set-password alice
```

The subject the clients will know Alice by is generated and stable. You pass `--subject` only when you are
importing an identity that already has one somewhere else.

[:beffroi-arrow-right: Keys, in full](../core/keys.md)
