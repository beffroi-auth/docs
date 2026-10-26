---
title: Pairwise subjects
description: The same person under a different identifier per sector, OIDC Core §8.1: how a client chooses the kind, how the identifier is computed, what the sector is, and what keeps it stable.
---

# Pairwise subjects

The `sub` a client receives for a person depends on the kind of subject identifier it registered (OIDC Core
§8). With `public`, every client sees the identifier the account carries. With `pairwise`, each sector sees
an identifier of its own, so that two clients of two sectors hold two different strings for one person and
cannot find out they are looking at the same one by comparing them (OIDC Core §8.1).

## Choosing the kind

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        billing:
            # ...
            subject_type: pairwise
```

`subject_type` is `public` or `pairwise`, the two kinds the bundle wires, which the discovery document lists
in `subject_types_supported` in that order. A client that registers none takes the first, `public`. A client
that registers itself may send the member too. A kind nothing wires is refused when the client is read,
rather than served an identifier of another kind.

## The identifier

A pairwise identifier is the SHA-256 of three things, written in base64url:

```
BASE64URL(SHA256(sector || subject of the account || salt of the tenant))
```

It is computed and never drawn, so it is the same identifier after a restore of the database, after an import
that keeps the subjects of the accounts, and in every worker at once. One person has one identifier per
sector, and two clients of one sector see that person under the same one. It is the `sub` of every document
written for the client: the ID token, the self-contained access token, the UserInfo answer, and the
introspection of its tokens.

## The sector

The sector is a host, never a URL, read from what the client registered, the first of these that answers:

| What the client registered | Its sector |
|---|---|
| A `sector_identifier_uri` | The host of that URI |
| Redirect URIs, all on one host | That host |
| No redirect URI, and a `jwks_uri` | The host of the `jwks_uri` (CIBA Core §4), which is how a client of the backchannel flow, sending no browser anywhere, has a sector |

A `pairwise` client whose redirect URIs are on several hosts and who registered no `sector_identifier_uri`
names no sector, and neither does one that registered no redirect URI and no `jwks_uri`: both are refused when
the client is read, rather than served an identifier computed from whichever value came first, because the
sector decides which clients see a person under the same identifier.

**Clients that must recognise the same people share a sector.** Clients whose redirect URIs are all on one
host are of that host's sector already. Clients on several hosts register one `sector_identifier_uri` on a
host of their own, the same for all of them, behind which the document lists the redirect URIs of every one
of them (OIDC Registration §5): they are then of that host's sector, and see a person under one identifier.

**A sector is a claim a registered client proves.** A client that [registers
itself](dynamic-registration.md) with a `sector_identifier_uri` publishes behind it the JSON array of URIs of
OIDC Registration §5, and the array lists every redirect URI the client registers, or its `jwks_uri` when it
registers no redirect URI. The provider reads it once, when the registration or its replacement is written,
with one `GET` that follows no redirect, within `client_registration.sector_identifier_timeout`, three
seconds by default, and `client_registration.sector_identifier_max_size`, 65536 bytes by default. A document
that cannot be read, that is not an array of strings, or that leaves one of those URIs out, refuses the
registration with `invalid_client_metadata`. Without that proof, a client able to name any sector could put
itself in another's and read its users under their identifiers. A client the deployment declares is not
asked for the document: the deployment answers for what it declares, and the host of the URI is its sector.

## The salt

The salt is a secret of the tenant: 256 random bits, drawn the first time the tenant needs it and never
again, sealed by the key management service of the tenant, and kept as a file beside its sealed keys,
`<keys.storage>/<tenant slug>/pairwise.salt`. Two workers that draw at the same moment leave one salt, the one
written first, and the other reads it back. The same salt computes the persistent `NameID` the [SAML identity
provider](../saml/identity-provider.md) gives a service provider, from other inputs, so that no identifier of
one is an identifier of the other, and whichever of the two is computed first draws it.

!!! warning "Back the salt up with the keys"

    A salt lost, or replaced by another, changes every pairwise identifier of the tenant: nothing leaks, but
    every client that attached an account to the identifiers it held stops recognising its users. Two
    deployments that share a salt give the same identifier to the same subject in the same sector.

## The way back

A hash goes one way, so a `sub` a client presents cannot be turned back into a person by computing anything.
The first time an identifier is written for a sector, the provider records which person it names in that
sector, in the `beffroi_pairwise_subject` table, and reads it back from there. A `sub` is always read for the
client that presents it, in that client's sector and in no other:

- a `login_hint` read as a `sub` ([interactions](interactions.md)) names somebody only when the client sending
  it was given that identifier, or a client of its sector was;
- an `id_token_hint`, at the authorization endpoint ([interactions](interactions.md)) and at the end session
  endpoint ([logout](logout.md)), names the person signed in when its `sub` is the identifier the client it was
  issued to holds of that person;
- the hints of a [backchannel authentication](grants/backchannel-authentication.md) request are read the same
  way;
- a self-contained access token somebody signed in for is found to be that person's by its `sub`, read for
  the client it was issued to. An opaque access token names its person in its record, and a self-contained
  one whose `sub` another client named carries its person sealed, so neither is looked up.

[:beffroi-arrow-right: Clients](clients.md) and [scopes and claims](scopes-and-claims.md)
