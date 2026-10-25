---
title: Microsoft Entra ID
description: Entra federating its guests to Beffroi as their SAML identity provider, and Entra ID as the upstream identity provider of a tenant through an enterprise application.
---

# Microsoft Entra ID

Entra ID meets Beffroi in both directions. It can federate the guests of a Microsoft tenant to Beffroi, which
is then their identity provider; and an enterprise application of Entra can be the upstream identity provider
of a tenant of Beffroi, for the people of the domains it answers for. Both have been played against a
Microsoft tenant, and what Entra needs that its documentation does not say is built into the provider rather
than left to a setting.

## Entra federating its guests to Beffroi

Here Entra is a service provider of the tenant: a guest of the Microsoft tenant is sent to Beffroi to sign in,
through the SAML/WS-Fed identity provider federation of Entra External ID.

### The service provider Entra is

Entra publishes no metadata for this federation, so they are written by hand, from what Microsoft documents,
and declared as a file of the deployment.

``` xml title="config/saml/entra-guest-federation-sp.xml"
<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="https://login.microsoftonline.com/00000000-0000-0000-0000-000000000000/">
  <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:persistent</md:NameIDFormat>
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="https://login.microsoftonline.com/login.srf" index="0" isDefault="true"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>
```

| What | Why |
|---|---|
| The entity ID is `https://login.microsoftonline.com/` followed by the ID of the Microsoft tenant and a slash | It is the `Issuer` of the requests Entra sends for a new federation, and the `Audience` it expects; the final slash is part of it |
| One assertion consumer service, `login.srf`, on HTTP-POST | Where Entra receives the response |
| No key | Entra does not sign the requests of this federation |
| No single logout service | Nothing documents single logout for it, and a service listed is one a `LogoutRequest` would be sent to |

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    saml:
        identity_provider: true
        service_providers:
            'https://login.microsoftonline.com/00000000-0000-0000-0000-000000000000/':
                metadata: '%kernel.project_dir%/config/saml/entra-guest-federation-sp.xml'
                signs_authn_requests: false
                attributes:
                    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress':
                        claim: email
```

`signs_authn_requests: false` is what lets an unsigned request in, from this service provider and no other.
The one attribute Entra requires is the e-mail address of the guest, under its claim type. Then read the
metadata:

``` bash
bin/console beffroi:saml:service-provider:refresh
```

### What the Entra portal takes

| Field of the portal | What to give it |
|---|---|
| Issuer URI | The entity ID of the identity provider of the tenant, `https://op.example.com/saml/metadata` |
| Passive authentication endpoint | Its single sign-on service, `https://op.example.com/saml/sso` |
| Signing certificate | The base64 of the certificate of the active SAML key, as the metadata publish it |
| Metadata URL | Optional. Microsoft's service reads it, so a provider Microsoft cannot reach offers none |

### What Entra asks that it does not document

Each is how the provider behaves for every service provider, with no setting to turn it off:

- **Every signature carries the certificate.** A response whose signatures carry no `KeyInfo` is refused by
  Entra with `AADSTS5000810: Unable to verify token signature. Signing key identifier is missing.`
- **The `Conditions` carry a `NotBefore`.** An assertion without one is refused with `AADSTS500089`.
- **The certificate expires.** The portal refused a certificate valid until the year 9999, written in
  `GeneralizedTime`, whether for the date or for its encoding; the one around the SAML key is valid ten years,
  written in `UTCTime`.
- **The request is posted from Entra's site, unsigned**, with a `RelayState` of several hundred bytes: it is
  posted again from the provider's own origin, so the session cookie comes with it, and its `RelayState` is
  given back as it came.
- **The page that posts the response names no `form-action`**, since `login.srf` sends the browser on to the
  client that asked Entra, an origin nothing declares.

### A rotation of the SAML key

The federation holds **one** signing certificate. With a metadata URL Microsoft can reach, Entra renews it
when it is about to expire; at a rotation it does not, and the certificate is replaced by hand, at the moment
the next key takes over, since the old certificate stops verifying the minute the new key signs.

That moment is known a week ahead: `beffroi:keys:list` shows when the staged SAML key activates, and
`beffroi:keys:activate` moves the take-over to the minute the administrator of the Microsoft tenant chooses.

## Entra ID as an upstream identity provider

Here Entra is the identity provider of an organisation, and the tenant of Beffroi is its service provider:
a person of the organisation's domain types their address on the login page and signs in at Microsoft.

### In the Entra portal

An enterprise application with SAML single sign-on:

| Field | Value |
|---|---|
| Identifier (Entity ID) | The entity ID of the service provider of the tenant, `https://op.example.com/saml/sp/metadata` |
| Reply URL (Assertion Consumer Service URL) | `https://op.example.com/saml/sp/acs` |
| Signing option | Sign the SAML response and the assertion, under SHA-256 |

The Federation Metadata XML of the application is what the tenant reads. Its entity ID is
`https://sts.windows.net/` followed by the ID of the Microsoft tenant and a slash. It is signed but carries no
`validUntil`, which metadata verified under pinned signers must carry, so it is trusted by the channel it came
through and `metadata_signers` stays empty. A certificate rolled over in the portal is a new document to read.

### The declaration

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    saml:
        service_provider: true
        identity_providers:
            'https://sts.windows.net/00000000-0000-0000-0000-000000000000/':
                metadata: '%kernel.project_dir%/config/saml/entra-idp.xml'
                domains: ['example.org']
                email_attribute: 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress'
                subject_attribute: 'http://schemas.microsoft.com/identity/claims/objectidentifier'
                profile:
                    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname': given_name
                    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname': family_name
                groups:
                    attribute: 'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups'
                    map:
                        '11111111-1111-1111-1111-111111111111': finance
                address_parameter: login_hint
```

| Option | Why this value |
|---|---|
| `domains` | The domain of the addresses of the organisation's people |
| `email_attribute` | The claim type Entra sends the user's mail under. Every attribute is named by its claim type, the URI, and not by the short name the portal shows |
| `subject_attribute` | The request asks for a persistent `NameID`, which Entra answers with an identifier of the person for this application: that is the subject. Should the application be set to send its `NameID` in another format, the e-mail address its portal offers among them, the object ID of the user, a value that does not change, names the person instead. A persistent `NameID` whose value is the address of the person is refused |
| `groups` | Entra sends security groups as their object IDs, which a group renamed in the portal does not change, so the map is keyed by object ID |
| `address_parameter` | Entra reads `login_hint` on its sign-in URL and prefills its form with it, so the person types their address once |

Create the groups the map names, then read the metadata:

``` bash
bin/console beffroi:group:create finance
bin/console beffroi:saml:identity-provider:refresh
```
