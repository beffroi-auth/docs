---
title: Tenants
description: The unit everything belongs to, the variables that declare it and its row in the database, the acr vocabulary it answers with, and the floor of its logins.
---

# Tenants

A tenant is the unit of isolation: it owns an issuer, a set of keys, a population of people, the clients that
may ask about them and the SAML peers it trusts. Nothing crosses from one tenant to another, and a subject
identifier is only meaningful inside the one that minted it. A deployment serves one tenant, the one its
variables declare.

## What the configuration says

The tenant is what the variables of the deployment say it is, and the image names one, `default`, under the
issuer of the development stack, so a deployment names at least its own issuer. One that names the rest as
well writes:

``` dotenv
BEFFROI_ISSUER=https://op.example.com
BEFFROI_TENANT_SLUG=default
BEFFROI_TENANT_NAME=Example
BEFFROI_TENANT_LOGO_URI=https://www.example.com/logo.svg
BEFFROI_TENANT_PRIMARY_COLOR='#1b4b8f'
BEFFROI_TENANT_PRIMARY_CONTENT_COLOR='#ffffff'
BEFFROI_TENANT_SELF_SERVED_CLAIMS='["name","given_name","family_name","locale","zoneinfo"]'
```

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_ISSUER` | `https://op.localhost` | The issuer identifier (OIDC Discovery 1.0 §3): an absolute `https` URL with no query, no fragment and no trailing slash, plain HTTP on a loopback host only. Every endpoint is served under it, the SAML metadata included |
| `BEFFROI_TENANT_SLUG` | `default` | The stable name of the tenant, from which its identifier is derived. Renaming it is creating another tenant |
| `BEFFROI_TENANT_NAME` | empty | What the pages call it. Empty, the host of the issuer |
| `BEFFROI_TENANT_LOGO_URI` | empty | The logo every page shows, an absolute `https` URL with no fragment and no credentials, plain HTTP on a loopback host only. Empty, the placeholder mark the image serves at `/tenant-logo.svg` under the issuer. The logo is loaded by the browser of the visitor, never by the provider |
| `BEFFROI_TENANT_PRIMARY_COLOR` | `#1f6feb` | The colour the buttons and the links of the pages are drawn in: `#` and three or six hexadecimal digits |
| `BEFFROI_TENANT_PRIMARY_CONTENT_COLOR` | `#ffffff` | The colour of what is written on it, in the same notation. The two colours are named together or not at all, and two empty variables are no colour, the pages keeping their own |
| `BEFFROI_TENANT_SELF_SERVED_CLAIMS` | the fourteen claims of OIDC Core §5.1 the application lets a person change, from `name` to `phone_number` | The claims the people of this tenant may change of themselves on the page of their account, a JSON list. A tenant whose directory owns the data opens none, `[]` |
| `BEFFROI_TENANT_AUTHENTICATION_CLASSES` | `{}` | The `acr` vocabulary of the tenant, below. `{}` is the default policy |
| `BEFFROI_TENANT_SCOPES` | `[]` | The [scopes](../oidc/scopes-and-claims.md#scopes) of the APIs the tenant protects, a JSON list. The tenant hands out tokens for them beside `openid`, the scopes of its claims and `offline_access`, announces them, and a client that registers itself may register them |

[Configuration](../application/configuration.md) lists the same variables among the others of the image,
`BEFFROI_ISSUER` and `BEFFROI_TENANT_SLUG` under [the provider](../application/configuration.md#the-provider)
and the others under [the tenant](../application/configuration.md#the-tenant).

## Its row

The variables declare the tenant, and a row of the database holds what the rest of the model points at. Six
settings are written in that row beside the issuer: the name, the logo, the two colours, the claims a person
changes of themselves and the `acr` classes. One command makes the row say what the variables say:

``` bash
bin/console beffroi:tenant:synchronize
```

It creates the row the first time, afterwards writes those of the six that changed, prints the tenant it
synchronised, and is safe to run at every deployment. Every request, command and message compares the row with
the environment of its process: while the two differ, each one that reads the tenant fails, and the log names
the setting that differs, `look` for the logo and the colours, while the timed steps wait. Changing one of the
six is therefore a restart of every process with the new value, and the command run in one of them. The issuer
is the one thing the command never changes: every token a tenant issued names it, so the command refuses
another, and another issuer is another tenant, under another slug. What a command decides with a date, the
floor of its logins below, is written on the row and nowhere else.

## The classes it answers with

A session never stores an `acr`: it records what was proven, and satisfies every class whose predicate holds
on those proofs. The predicates are the provider's, one class each, and a tenant names its classes on them.

| Predicate | What it requires | Its class in the default policy |
|---|---|---|
| `phishing_resistant_hardware` | A passkey bound to its authenticator | `phrh` (OpenID Connect EAP ACR Values 1.0) |
| `phishing_resistant` | A passkey, synced or bound | `phr` (OpenID Connect EAP ACR Values 1.0) |
| `two_factors` | Two methods of different kinds, knowledge, possession or inherence (RFC 8176 §2), or one that counts as several | `2` |
| `single_factor` | One method, whatever it is | `1` |

A tenant that names nothing, `{}` as in the image, answers with that default policy, strongest first. One that
names its own maps each class name to a predicate in `BEFFROI_TENANT_AUTHENTICATION_CLASSES`, in the order a
session is answered in:

``` dotenv
BEFFROI_TENANT_AUTHENTICATION_CLASSES='{"gold":"phishing_resistant","silver":"two_factors","bronze":"single_factor"}'
```

A name no wired predicate carries is refused by the first request or command that reads the tenant, naming the
ones that are wired, and `phr` or `phrh` on a predicate that is not their meaning is refused too: OIDC Core §2
forbids using a registered name in another sense. So is a policy with no class on `single_factor`, the one
predicate every login satisfies, since every session has an `acr`, and so is the name `0`. What the discovery
document announces in `acr_values_supported` is the classes of this policy the tenant can actually prove. The
classes are written in [the row](#its-row), so a change of them is followed by `beffroi:tenant:synchronize`.

## The floor of its logins

A tenant may require more of every login than a single factor, and name the predicate every login of its
people has to satisfy:

``` bash
bin/console beffroi:tenant:login-floor phishing_resistant
```

**A floor asks for more, never for something else.** It is a predicate, and a predicate only ever holds on
more proofs, so it can say "a passkey at least" and cannot say "a password and nothing else": the switch to do
it wrong is not expressible. A tenant that names no floor keeps `single_factor`, which every login
satisfies.

**What the floor forbids leaves the model.** The command asks before it runs, then forgets every credential
of the tenant that proves nothing the floor reads, its secret and its row: under `phishing_resistant`, every
password, one-time code and backup code goes, and nothing dormant is left to leak. The act stays in the
journal of each person, a credential revoked earlier stays where it was, and lowering the floor afterwards
gives nobody back what was forgotten.

**Everything reads it.**

- The core refuses a login under the floor wherever a login ends, so no second copy of the rule can drift. A
  password the floor reads nothing of is refused before anybody is named, at the cost of nothing.
- The login page offers only the logins the tenant admits: a tenant that signs its people in by passkey
  shows no password field and no username, the passkey naming its own user.
- A step-up offers no kind of credential the floor forbids, and the page of the second factor offers an
  enrolment only where a code is admitted.
- The length a password has to reach follows it: fifteen characters where a password signs somebody in
  alone, eight where a second factor goes with it (NIST SP 800-63B §3.1.1.2). A password already stored is
  left as it is, since a hash says nothing of the length behind it.
- A login through an [upstream identity provider](../saml/federated-sign-in.md#the-session) is held to it as
  well.

A person created after the floor was raised has nothing to sign in with yet. An [enrolment
ticket](credentials/passkeys.md#a-first-passkey-from-a-ticket) gives them their first passkey without a
password ever existing.

## The domains it federates

A tenant whose SAML service provider declares [upstream identity
providers](../saml/upstream-identity-providers.md) federates their domains: its people of those domains sign
in at their organisation's identity provider and through nothing else, and its login page asks for the
address first.
