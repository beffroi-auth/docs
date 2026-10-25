---
title: The identity provider
description: The tenant as a SAML identity provider, its signing key held by the key management service, the certificate around it, and the metadata service providers are configured from.
---

# The identity provider

The tenant is the SAML identity provider of the service providers it declares: they send it an
`AuthnRequest`, and it answers with a signed assertion about the person signed in. This page is the role
itself, its key and the document that describes it. [Service providers](service-providers.md) is how one is
declared, and [single sign-on](single-sign-on.md) what a request gets.

## Turning it on

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    saml:
        identity_provider:
            enabled: true
```

| Option | Default | What it decides |
|---|---|---|
| `enabled` | `false` | Whether the role exists at all. Off, nothing of it is wired: the metadata answer `404` and every message at its endpoints is refused as one of an issuer nobody declared |
| `want_authn_requests_signed` | `true` | What the metadata say in `WantAuthnRequestsSigned` (SAML Metadata §2.4.3) |
| `staging_delay` | `604800`, seven days | How long a new SAML signing key is published in the metadata before it signs, in seconds |
| `age` | `31536000`, 365 days | How long a SAML signing key works before a successor is staged behind it, in seconds, counted from its activation |
| `cache_duration` | `86400`, one day | The `cacheDuration` of the metadata (SAML Metadata §2.3.2), in seconds: how long a service provider keeps them before it fetches them again. One second at least, and strictly shorter than `staging_delay`, which the configuration refuses otherwise |

The three figures belong to the deployment and not to a tenant, as those of `beffroi.keys` do, and they are
the figures of the SAML key whichever role draws it: the [service provider](upstream-identity-providers.md)
of the tenant signs with the same key.

`want_authn_requests_signed` is an announcement, and nothing more. It tells a service provider configured
from the metadata to sign its requests, which is what a broker such as SimpleSAMLphp does when it reads
`true`. Whether a request that arrives needs a signature is decided per service provider, by its declaration
and its own metadata, and the setting neither adds a signature to that rule nor takes one from it:
[the signature a request needs](service-providers.md#the-signature-a-request-needs) says how.

## The key

The SAML signing key is a key of the tenant like every other one. Its algorithm is `SAML-SIGNING`, an RSA
key of 3072 bits, the size every RSA key of the tenant is drawn at. The key pair is drawn
in the process, its private half sealed by the key management service before anything is written, and
opened in memory when the process signs. It is not in the JWK Set and it is not in the metadata: what the
metadata publish is a certificate around its public half.

Turning a role on does not draw a key. On a deployment that has none, draw it once:

``` bash
bin/console beffroi:keys:generate --algorithm=SAML-SIGNING
```

From then on it lives the life of every key of the tenant, with the same commands:
`beffroi:keys:rotate --algorithm=SAML-SIGNING` stages a successor, `beffroi:keys:activate` brings a staged
key in before its date, `beffroi:keys:retire` takes a retiring one out, and the timed step stages a
successor on its own once the active key has worked its age. A tenant with no SAML key in service has no
metadata, and answers `404` there until it has one.

A deployment that turns both roles off after its tenant drew a key leaves that key where it is: nothing
serves it, rotates it or draws it again, and turning a role back on puts it back in service as it was.

[:beffroi-arrow-right: Keys, and the commands that rotate them](../core/keys.md)

## The certificate

A service provider identifies the key of an identity provider by an X.509 certificate, so each SAML key in
service is published inside one. It is the key's own: self-signed by that key, and verified under the public
half it carries before it is published.

| Field | Value |
|---|---|
| Subject and issuer | `CN=` the slug of the tenant |
| Validity | Ten years from the creation of the key, written as `UTCTime` |
| Extensions | `keyUsage` with `digitalSignature` alone, critical |
| Signature | `sha256WithRSAEncryption`, by the key itself |

Its bytes are a function of the key and of the tenant, so every process of the deployment publishes the
same certificate for the same key. The ten years are not how long the key works: the key signs for its
age, one year by default, and its status is what retires it. A certificate in metadata is how a key is
written down, and a service provider that follows the SAML V2.0 Metadata Interoperability Profile does not
evaluate its validity period (§2.6.1). Ten years is what hosted identity providers issue theirs for, and a
certificate dated to the year 9999, the form RFC 5280 §4.1.2.5 gives one that never expires, is one
Microsoft Entra ID refuses.

## The metadata

The metadata are served at `/saml/metadata`, and **that URL is the entity ID of the identity provider**: a
service provider resolves an entity ID to its metadata there (SAML Metadata §4.1), and keeps it. Changing
the issuer of a deployment is therefore a new identity provider for every service provider that knew the
old one.

``` text
https://op.example.com/saml/metadata
```

What they hold is read from the configuration of the tenant, never from the request that asked for them:

- one `md:EntityDescriptor` holding one `md:IDPSSODescriptor` of SAML 2.0;
- one `KeyDescriptor use="signing"` per SAML key in service, staged, active and retiring, in the order they
  were created;
- the single sign-on service at `/saml/sso` and the single logout service at `/saml/slo`, each listed with
  HTTP-Redirect and then HTTP-POST at the same URL;
- `WantAuthnRequestsSigned`, as the configuration says;
- one `NameIDFormat`, `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`, the only format the identity
  provider writes;
- the `cacheDuration` of the configuration, and no `validUntil`.

They carry no encryption certificate, since the identity provider decrypts nothing a service provider sends
it, and they are not signed: the key that would sign them is the key they publish, so a service provider
trusts them by the channel it read them through, the URL over TLS or the file an administrator gave it.
They are served as `application/samlmetadata+xml`, with `Cache-Control: public` and the `max-age` of the
JWK Set, five minutes unless `beffroi.keys.jwks_max_age` says otherwise, so a cache on the way never holds a
copy older than that.

The routes have to be mounted under the issuer, as the discovery document's are: the bundle refuses to
write metadata whose endpoints would not be.

## A rotation without an outage

A service provider that pinned the old certificate refuses everything the new key signs, so the next
certificate is published long before it is used.

``` mermaid
graph LR
  s["staged<br/><small>in the metadata,<br/>signs nothing</small>"] -- "seven days" --> a["active<br/><small>signs</small>"]
  a -- "365 days, then a successor<br/>is staged behind it" --> r["retiring<br/><small>still in the metadata</small>"]
  r --> x["retired"]
```

**Staged for seven days.** A rotation adds the certificate of the next key to the metadata a week before
that key signs anything. A service provider that honours the `cacheDuration` of one day fetches the
metadata again six times in that week, so a refresh that fails, or a job that did not run over a weekend,
still leaves it days to take the next certificate.

**A week is also what a person needs.** A service provider whose administrator uploaded the certificate by
hand, rather than pointing it at the metadata, has the staging window to put the next one in place.
`beffroi:keys:list` shows the date the staged key takes over, and `beffroi:keys:activate` moves it to the
minute the administrator chooses.

**A year of work.** Every rotation is a step for whoever pinned a certificate, so the SAML key works 365
days, inside the one to three years NIST SP 800-57 Part 1 Rev. 5 §5.3.6 gives a private signature key, where
the other keys of the tenant work ninety. Those keep the figures of `beffroi.keys`, and a rotation of one of
them is not slowed by the SAML key.

The key management service is not asked at every login: a process opens the active key once to sign and
keeps it open, as it does the keys that sign tokens.
