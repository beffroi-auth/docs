---
title: Service providers
description: Declaring a SAML service provider, reading its metadata and keeping them fresh, the attributes it receives, the signature its requests need and the encryption it asks for.
---

# Service providers

A service provider is an application that signs its users in through the [identity
provider](identity-provider.md) of the tenant. It exists here because the deployment declares it, keyed by
its entity ID as a client of OpenID Connect is keyed by its `client_id`. No request registers one and no page
edits one: a peer that may obtain an assertion about anybody is a decision of whoever runs the deployment.

## Declaring one

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    saml:
        identity_provider: true
        service_providers:
            'https://sp.example.com/saml/metadata':
                metadata: 'https://sp.example.com/saml/metadata'
                attributes:
                    'urn:oid:0.9.2342.19200300.100.1.1':
                        claim: preferred_username
                        friendly_name: uid
                    'urn:oid:0.9.2342.19200300.100.1.3':
                        claim: email
                        friendly_name: mail
                    'urn:oid:2.16.840.1.113730.3.1.241':
                        claim: name
                        friendly_name: displayName
```

| Option | Default | What it decides |
|---|---|---|
| The key | | The entity ID of the service provider, compared exactly with the one its metadata carry: at most 1024 characters, no whitespace |
| `metadata` | required | Where its metadata are read from: an `https` URL, or the absolute path of a file of the deployment. Nothing else, a plain `http` URL included |
| `metadata_signers` | none | The certificates the metadata are signed by, each the base64 of its DER as an `X509Certificate` carries it, sixteen at most. Named, the metadata are verified under them; left empty, they are trusted by the channel they come through |
| `attributes` | none | The claims sent to this service provider, keyed by the name of the attribute each one is sent as, 256 at most |
| `encrypt_assertions` | `false` | Its assertions are encrypted for a key of its metadata |
| `signs_authn_requests` | `true` | It signs its authentication requests |

A declaration is refused while the identity provider of the tenant is not enabled, and a declaration that
does not hold together fails the build of the deployment rather than its first login: when the container is
compiled for every rule, and right after it, in the same build, for the claims the attributes name. A
declaration that holds an environment variable, whose value only the running deployment knows, is held to
the same rules at its first use.

## Its metadata

The declaration says where the metadata are; what they say is read there, and nowhere else. They are where
the assertion consumer services of the service provider are, its single logout services, and the keys its
requests are verified with: the declaration names none of them, so a service provider cannot be sent an
assertion anywhere its own metadata do not list.

**Read before the first login.** A service provider whose metadata have never been accepted is refused, so
a declaration is followed by a reading:

``` bash
bin/console beffroi:saml:service-provider:refresh
bin/console beffroi:saml:service-provider:refresh 'https://sp.example.com/saml/metadata'
```

Without an argument it reads every service provider the configuration declares. Each one is reported as
registered, registered by another process meanwhile, refreshed, unchanged, refused or failed, and a refusal
names the rule it broke and never a value of the document. A timed step does the same every hour, for the
service providers and the [upstream identity providers](upstream-identity-providers.md) alike, and writes a
refusal to the log as an error: the refused document comes back at every hour while the accepted one goes
on serving, which is something an operator wants to be alerted on.

**How they are fetched.** A file is read whole. A URL is fetched with one `GET`, no redirect followed, ten
seconds at most, any status but `2xx` refused, and the body refused as soon as it passes one mebibyte.

**What is refused**, at the first reading as at every refresh, the accepted document being kept each time:

- a document whose entity ID is not the declared one, or that holds no `md:SPSSODescriptor` of SAML 2.0;
- a document past its `validUntil`, or past the `validUntil` of its service provider role;
- an assertion consumer service or a single logout service that is not `https` on a host, with no
  userinfo;
- metadata with no key for encryption, for a declaration that asks for encrypted assertions;
- metadata with no key for signing, for a service provider whose requests need a signature;
- a document read under pinned signers that carries no `validUntil`, or whose `validUntil` is earlier than
  the one of the document already accepted.

Endpoints on other bindings than HTTP-Redirect and HTTP-POST are dropped, and the other role descriptors
skipped, so that the metadata of a real deployment load.

**Signed metadata never go back.** An older document signed by the same key verifies as well as the newer
one, so under pinned signers a document older than the accepted one is refused, which is the rollback the
signature cannot catch by itself. Metadata trusted by their channel follow the channel instead: the next
reading replaces the accepted document whatever its `validUntil`, so that a document planted while somebody
else held the host gives way at the first refresh after the host is the service provider's again.

**Only a person goes back on it.** Forgetting the accepted document is a command run by hand, never a step
of the schedule nor a request, and the next reading then registers the service provider as a first one:

``` bash
bin/console beffroi:saml:service-provider:forget 'https://sp.example.com/saml/metadata'
```

An entity ID for which nothing is accepted is answered so, and the command fails, so a mistyped entity ID is
never taken for a forgotten one. A declaration removed from the configuration leaves its accepted document
where it is, read by nothing, until an operator forgets it.

**Sealed where it sits.** The document is kept as the bytes that were read and sealed under the data key of
the tenant, since an `md:ContactPerson` names people.

## The attributes it receives

An assertion carries one `Attribute` per mapping whose claim the person holds, under the name, the name
format and the friendly name the mapping gives, and nothing else. A claim may be sent under several names.

| Key | Default | What it is |
|---|---|---|
| `claim` | required | The name of the claim, as OpenID Connect names it (OIDC Core §5.1). The claims are the ones the provider serves to OpenID Connect, so a claim a deployment adds can be mapped the day its class is wired |
| `name_format` | `uri` | The name format of the attribute (SAML Core §8.2): `uri`, under which the name is an absolute URI, as the SAML V2.0 interoperability profiles ask; `basic`; or `unspecified` |
| `friendly_name` | none | A name a person reads (SAML Core §2.7.3.1), which nothing compares |

A value is the text of the claim: a string as it is, an integer in decimal, a boolean as `true` or `false`,
and a list as one value per member. A value holding a character XML 1.0 cannot carry, a control character
other than the tab and the line breaks or bytes that are not UTF-8, is not sent, and neither is a claim that
is an object, such as `address`. The refusal goes to the log, naming the service provider, the claim and the
rule but never the value, and the sign-on goes on without that attribute: an attribute is the person's
statement to that service provider, and one cut short or rewritten on the way would be a statement they
never made.

## The signature a request needs

An `AuthnRequest` needs a signature, in its XML or over the query string of HTTP-Redirect, unless both the
service provider and its metadata say it does not sign. Whichever of the two says it signs wins:

| `signs_authn_requests` | `AuthnRequestsSigned` of its metadata | An unsigned request |
|---|---|---|
| `true`, the default | anything | refused |
| `false` | `true` | refused |
| `false` | `false` or absent | accepted |

Nothing else decides it, neither the `WantAuthnRequestsSigned` the identity provider announces nor any
setting of the tenant or of the deployment. A signature a request does carry is verified whatever the rule
says, under the keys of the metadata and never under a key the message names.

`signs_authn_requests: false` exists for the service providers that cannot sign, [Microsoft Entra
ID](microsoft-entra-id.md) federating its guests among them. A logout request is another matter: it is
always signed, whatever the declaration says of the sign-on.

## The encryption it asks for

`encrypt_assertions: true` has every assertion of that service provider sent as a `saml:EncryptedAssertion`,
never in clear. The declaration decides whether the assertions are encrypted; the metadata only decide which
key they are encrypted for, which is the first certificate for encryption they list, read again when the
response is written so that a key a refresh put in place meanwhile is the one used. A service provider that
does not ask gets its assertions in clear, whatever keys its metadata hold.

| What | Value |
|---|---|
| The content | `http://www.w3.org/2009/xmlenc11#aes256-gcm`, a fresh key and IV for every assertion |
| The key | `http://www.w3.org/2001/04/xmlenc#rsa-oaep-mgf1p`, whose mask is computed with SHA-1: it is what PHP wraps a key under and what SimpleSAMLphp unwraps, and the hash inside OAEP rests on no collision resistance |
| The order | The assertion is signed, then encrypted with its signature inside, then the response is signed over the ciphertext (SAML Core §6.2) |

The `md:EncryptionMethod` elements of the metadata are not read, so no scheme is negotiated and none is
downgraded: a service provider that cannot decrypt AES-GCM gets nothing it can read rather than an assertion
in CBC. A request of a service provider that asks for encryption while its metadata hold no key for it is
refused before anybody signs in, and nothing is sent in clear.
