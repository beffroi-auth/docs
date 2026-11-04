---
title: Upstream identity providers
description: The tenant as a SAML service provider, its metadata, the identity providers upstream of it that it trusts for the people of their domains, and the key each of them encrypts for.
---

# Upstream identity providers

The tenant can sign a person in against the SAML identity provider of their organisation rather than with a
credential of its own. For that it is a service provider, to the identity providers the deployment declares
upstream of it, each one answering for the e-mail domains it names. This page is the role and its peers;
[signing in through an organisation](federated-sign-in.md) is what a person goes through.

## Turning it on

The image is no service provider, and a deployment turns the role on with:

``` dotenv
BEFFROI_SAML_SERVICE_PROVIDER=true
```

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_SAML_SERVICE_PROVIDER` | `false` | Whether the role is on, `true` or `false`, an empty variable reading `false`. Its routes and services are always wired; off, it serves nothing, and its metadata, its assertion consumer service and its sign-on answer `404`. It is read when a process builds what the role changes, so turning the role on or off asks for a restart and not for a new image |
| `BEFFROI_SAML_SERVICE_PROVIDER_ENTITY_ID` | empty | The entity ID of the service provider, for one its identity providers already know by a name it keeps: an absolute URI of 1024 characters at most, with no whitespace, control, format or invisible character. Empty, the URL of its metadata |

The service provider signs with the SAML signing key of the [identity provider](identity-provider.md#the-key),
one key for both roles, rotated by `BEFFROI_SAML_KEY_STAGING_DELAY` and `BEFFROI_SAML_KEY_AGE` whichever role
is on. A deployment that serves only this role draws that key the same way:

``` bash
bin/console beffroi:keys:generate --algorithm=SAML-SIGNING
```

The two roles are two entities. The entity ID of the service provider is never the one of the identity
provider of the tenant, which the provider refuses the first time it locates its service provider, whether
the identity provider is on or not, so turning it on later never makes the two one.

## Its metadata

Served at `/saml/sp/metadata`, which is also its entity ID unless `BEFFROI_SAML_SERVICE_PROVIDER_ENTITY_ID`
names another. They hold:

- one `md:SPSSODescriptor` of SAML 2.0, with `AuthnRequestsSigned="true"`, since every request it sends is
  signed, and `WantAssertionsSigned="true"`, so that an identity provider configured from them signs its
  assertion;
- one `KeyDescriptor use="signing"` per SAML key in service, as the identity provider's metadata list them;
- one assertion consumer service, on HTTP-POST, at `/saml/sp/acs`;
- the `cacheDuration` of the identity provider's metadata, `BEFFROI_SAML_METADATA_CACHE_DURATION`, and no
  `validUntil`.

They list no single logout service, single logout with an upstream identity provider not being served, and
no key for encryption: the certificate an identity provider encrypts for is published to that provider alone,
below. Like the identity provider's, they are unsigned, and every URL in them comes from the issuer of the
tenant and the variables above, never from the request that asked for them.

## Declaring an identity provider

An upstream identity provider is declared in `BEFFROI_SAML_IDENTITY_PROVIDERS`, a JSON document keyed by
entity ID, `{}` in the image, beside the variable that turns the role on:

``` dotenv
BEFFROI_SAML_SERVICE_PROVIDER=true
```

``` json title="BEFFROI_SAML_IDENTITY_PROVIDERS"
{
    "https://idp.example.org/saml/metadata": {
        "metadata": "https://idp.example.org/saml/metadata",
        "domains": ["example.org"],
        "email_attribute": "mail",
        "profile": {"givenName": "given_name", "sn": "family_name"},
        "groups": {"attribute": "memberOf", "map": {"staff": "Staff"}}
    }
}
```

The document is the value of the variable, written on one line or over several as [lists in
JSON](../application/examples.md#lists-in-json) are.

| Member | Default | What it decides |
|---|---|---|
| The key | | The entity ID of the identity provider, compared exactly with the one of its metadata. Never an entity ID of the tenant itself |
| `metadata` | required | Where its metadata are read from: an `https` URL, no redirect followed. The declaration takes the absolute path of a file as well, and the image carries no file of a peer, so a deployment of the image names a URL |
| `metadata_signers` | none | The certificates its metadata are signed by, each the base64 of its DER. Named, the metadata are verified under them and must carry a `validUntil` |
| `domains` | required | The e-mail domains it answers for, one at least and 256 at most |
| `email_attribute` | required | The name of the attribute that carries the e-mail address of a person |
| `profile` | none | The attributes that fill the profile of a person, keyed by the name of the attribute, each naming the claim it fills |
| `subject_attribute` | none | The attribute that names a person when the `NameID` of an assertion is not persistent |
| `groups` | none | The attribute that carries the groups of a person, and the group of the tenant each of its values stands for |
| `require_encrypted_assertions` | `false` | An assertion arrives encrypted, or it is refused |
| `address_parameter` | none | The parameter of its single sign-on service that takes the address the person typed, which it prefills its sign-in with |

The list is read when a process first needs it, and held there to the rules of its members, those below and
the claims of `profile` included: a declaration that does not hold together is refused, naming its identity
provider. The whole list is refused, wherever it is read, the login page among them, when it declares an
identity provider while `BEFFROI_SAML_SERVICE_PROVIDER` turns the role off, so a deployment that turns the
role off empties the list in the same change. The reading below is a first one, so a declaration that does not
hold is refused there rather than at a login.

**Domains.** A domain is a name of the DNS, read without regard to case, a name outside ASCII written as its
A-label. It is the whole part of an address after its `@` and nothing under it: `example.org` does not answer
for `eu.example.org`, which a provider that answers for it declares too. A domain answers to one identity
provider of the tenant, and a domain two of them declare is refused, naming it and both providers: which
provider answers for an address is never a choice.

**The profile.** One attribute per claim, among the fourteen claims of a profile the application wires,
whatever the tenant lets its people change of themselves: `name`, `given_name`, `family_name`, `middle_name`,
`nickname`, `preferred_username`, `birthdate`, `gender`, `locale`, `zoneinfo`, `profile`, `picture`,
`website` and `phone_number`. `email` is not among them, since `email_attribute` carries it. A telephone
number is written unverified: the provider filling it is not a proof that anybody verified it.

**The subject.** A person is named at their identity provider by a persistent `NameID`, a value it keeps for
them. For an identity provider that sends another format, `subject_attribute` names the attribute that does
the same job: a value that never changes, such as the object identifier Microsoft Entra ID sends, and never an
address. The attribute of the e-mail is refused there, since an address is given again to somebody else, and
the person hired under the address of one who left would be signed in to the account of that person.

**Groups.** Each value of the attribute is compared exactly with the keys of `map`, 256 values at most, and a
value the map does not name is no group. The groups the map names are groups of the tenant, found by their
name, and none is ever created from what an identity provider sends: create them first.

``` bash
bin/console beffroi:group:create Staff
```

## Its metadata, read and kept

Exactly as a [service provider's](service-providers.md#its-metadata) are, by the same objects: read from the
declared location, verified under pinned signers or trusted by their channel, refused when expired, never
older than the document accepted when they are signed, sealed where they sit, and refreshed every hour by the
timed step. They are refused besides when they hold no `md:IDPSSODescriptor` of SAML 2.0, no key for signing,
or a single sign-on service that is not `https` on a host.

``` bash
bin/console beffroi:saml:identity-provider:refresh
bin/console beffroi:saml:identity-provider:forget 'https://idp.example.org/saml/metadata'
```

An identity provider whose metadata were never accepted cannot be signed in through: read them before
announcing the domain to anybody.

## The key it encrypts for

An identity provider that encrypts its assertions encrypts them for a key of the tenant, and each identity
provider has one of its own, never shared with another nor with the signing key. Its algorithm names the
provider:

``` bash
bin/console beffroi:keys:generate --algorithm='SAML-ENCRYPTION:https://idp.example.org/saml/metadata'
```

It is an RSA key of the tenant like the others, sealed by the key management service, absent from the JWK Set
so that no OpenID Connect client encrypts to it, and rotated with the commands and the timed step of every
key, by the figures of the SAML signing key: seven days staged and a year of work in the image.

**Its certificate goes to that provider alone.** The metadata of the service provider for one identity
provider are served at `/saml/sp/metadata/` followed by the entity ID of that provider in base64url, without
padding (RFC 4648 §5):

``` bash
printf '%s' 'https://idp.example.org/saml/metadata' | basenc --base64url --wrap=0 | tr -d '='
```

They are the metadata above, with one `KeyDescriptor use="encryption"` per key of that provider staged or
active, the newest first, and none of another provider. An identity provider takes the first certificate it
finds, so listing the staged key first is what makes it encrypt for the next key days before that key takes
over; the retiring key is no longer announced, and still opens what was encrypted for it until it retires.
The certificate is self-signed, its one extension `keyUsage` with `keyEncipherment` alone. The URL answers
`404` while the tenant holds no key in service for that provider.

**A ciphertext of a provider is opened by the keys of that provider, and by no other.** The keys tried are
those of the identity provider whose metadata verified the response, its staged, active and retiring ones in
turn; the `KeyInfo` of the encrypted key is not read. A key shared between two providers would let one of them
carry the other's ciphertext under its own signature and read what the decryption answers, which is why there
is one key per provider.

| What arrives | What happens |
|---|---|
| AES-GCM, its key under RSA-OAEP | Decrypted |
| AES-CBC, in a response whose own signature verifies | Decrypted, the signature covering the ciphertext. Entra, AD FS and SimpleSAMLphp encrypt under CBC |
| AES-CBC, in a response that is not signed | Refused by name: CBC authenticates nothing, so it is opened only under a signature |
| An encrypted assertion from a provider the tenant holds no key for | Refused by name |
| An assertion in clear from a provider declared with `require_encrypted_assertions` set to `true` | Refused before anything of it is read |

Every cryptographic failure of a decryption is one and the same refusal, so that nothing in the answer tells
a padding from a key.
