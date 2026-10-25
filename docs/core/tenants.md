---
title: Tenants
description: The unit everything belongs to, what is configuration and what is its row, the acr vocabulary it answers with, and the floor of its logins.
---

# Tenants

A tenant is the unit of isolation: it owns an issuer, a set of keys, a population of people, the clients that
may ask about them and the SAML peers it trusts. Nothing crosses from one tenant to another, and a subject
identifier is only meaningful inside the one that minted it. A deployment serves one tenant today, the one its
configuration declares.

## What the configuration says

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tenant:
        issuer: '%env(BEFFROI_ISSUER)%'
        slug: default
        name: 'Example'
        look:
            logo_uri: 'https://www.example.com/logo.svg'
            primary_color: '#1b4b8f'
            primary_content_color: '#ffffff'
        self_served_claims: [name, given_name, family_name, locale, zoneinfo]
```

| Option | Default | What it decides |
|---|---|---|
| `issuer` | required | The issuer identifier (OIDC Discovery 1.0 §3): an absolute `https` URL with no query, no fragment and no trailing slash, plain HTTP on a loopback host only. Every endpoint is served under it, the SAML metadata included |
| `slug` | `default` | The stable name of the tenant, from which its identifier is derived. Renaming it is creating another tenant |
| `name` | the host of the issuer | What the pages call it |
| `look` | none | The logo and the two colours every page shows. The logo is loaded by the browser of the visitor, never by the provider, and the two colours are declared together or not at all |
| `self_served_claims` | none | The claims of OIDC Core §5.1 the people of this tenant may change of themselves on the page of their account. A tenant whose directory owns the data opens none |
| `authentication_classes` | the default policy | The `acr` vocabulary of the tenant, below |

## Its row

The configuration declares the tenant, and a row of the database holds what the rest of the model points at.
One command makes the row say what the configuration says:

``` bash
bin/console beffroi:tenant:synchronize
```

It reports what it did, created, renamed or left alone, and is safe to run at every deployment. What a
command decides with a date, the floor of its logins below, is written on the row and nowhere else.

## The classes it answers with

A session never stores an `acr`: it records what was proven, and satisfies every class whose predicate holds
on those proofs. The predicates are the provider's, one class each, and a tenant names its classes on them.

| Predicate | What it requires | Its class in the default policy |
|---|---|---|
| `phishing_resistant_hardware` | A passkey bound to its authenticator | `phrh` (OpenID Connect EAP ACR Values 1.0) |
| `phishing_resistant` | A passkey, synced or bound | `phr` (OpenID Connect EAP ACR Values 1.0) |
| `two_factors` | Two methods of different kinds, knowledge, possession or inherence (RFC 8176 §2), or one that counts as several | `2` |
| `single_factor` | One method, whatever it is | `1` |

A tenant that names nothing answers with that default policy, strongest first. One that names its own maps
each class name to a predicate:

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tenant:
        authentication_classes:
            gold: phishing_resistant
            silver: two_factors
            bronze: single_factor
```

A name no wired predicate carries refuses the start, naming the ones that are wired, and `phr` or `phrh` on a
predicate that is not their meaning is refused too: OIDC Core §2 forbids using a registered name in another
sense. What the discovery document announces in `acr_values_supported` is the classes of this policy the
tenant can actually prove.

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
