---
title: The SAML packages
description: xml-security, saml2-model and saml2-bindings, the libraries that carry the SAML format beneath the provider, what each one guarantees and how a project uses them on its own.
---

# The SAML packages

XML Signature and XML Encryption are the two specifications where a permissive reader becomes a
vulnerability: signature wrapping, entity expansion, a canonicalization that does not cover what the verifier
thinks it covers. So the format is written here, in three libraries with no SAML or XML Signature library
underneath, each held to a written specification of its own, and the profile the tenants use sits on top of
them.

| Package | Namespace | What it holds | Requires |
|---|---|---|---|
| `beffroi/xml-security` | `Beffroi\Xml` | `Core`, a safe DOM; `Dsig`, XML Signature; `Enc`, XML Encryption | PHP 8.4, `ext-dom`, `ext-libxml`, `ext-openssl` |
| `beffroi/saml2-model` | `Beffroi\Saml2\Model` | The `samlp:`, `saml:` and `md:` objects of Web Browser SSO and Single Logout, read strictly, validated and written. No HTTP | `xml-security`, `psr/clock` |
| `beffroi/saml2-bindings` | `Beffroi\Saml2\Bindings` | HTTP-Redirect and HTTP-POST, on strings and arrays, never on an HTTP object | `saml2-model`, `xml-security`, `ext-zlib` |
| `beffroi/saml` | `Beffroi\Saml` | The profile for the tenants: the identity provider and the service provider of a tenant, their metadata, the attributes, the `NameID`, single logout on the session of the core | the three above, `beffroi/core`, `spomky-labs/pki-framework`, `ext-intl` |

``` mermaid
graph RL
  saml["beffroi/saml"] --> bindings["saml2-bindings"]
  saml --> model["saml2-model"]
  saml --> xml["xml-security"]
  saml --> core["beffroi/core"]
  bindings --> model
  bindings --> xml
  model --> xml
```

The first three know nothing of Beffroi and are usable by any PHP project that speaks SAML. Each rule they
state is code, never an option, and each refusal names the rule it applies and never a value of the input, so
a message can be logged without what it carried.

## `xml-security`

**`Core` loads XML without being attacked.** It takes bytes, never a path or a stream, and refuses, before
anything reads the tree: a document type declaration anywhere in the bytes, an encoding other than UTF-8, an
XML version other than 1.0, any diagnostic of libxml at any level, and an input past its bounds.

| Bound | Default |
|---|---|
| Size | 1 MiB |
| Depth | 64 |
| Elements | 10 000 |
| Attributes per element | 32 |
| Namespace declarations | 512 |
| Length of an identifier | 128 bytes |

A document has one space of identifiers, built at load, in which a duplicate is refused, and an element is
found by identifier through that index, never by XPath and never by searching descendants. Text is the
concatenation of the text and CDATA children, comments skipped, so `user@example.com<!---->.evil.com` reads as
`user@example.com.evil.com`, the value the signature covers. Canonicalization knows the four methods of
Canonical XML 1.0 and Exclusive XML Canonicalization 1.0, with and without comments, and nothing ever
canonicalizes to the empty string.

**`Dsig` verifies only what the signature covers.** One reference, to the element that claims to be signed;
the enveloped signature and exclusive canonicalization transforms and no others; RSA with SHA-256, SHA-384 or
SHA-512, and RSASSA-PSS where PHP 8.5 and OpenSSL 3.1 provide it; RSA keys of 2048 bits at least. SHA-1, MD5,
HMAC, DSA, ECDSA, XPath and XSLT are refused before anything is computed. The key is the one the consumer
gives, never one the `KeyInfo` of the signature names, and what the consumer reads afterwards is the bytes
that were hashed, loaded again.

**`Enc` builds no oracle.** It writes AES-GCM, under RSA-OAEP, with fresh randomness for every message. It
reads AES-CBC only under a signature that covers the ciphertext and never writes it, and every cryptographic
failure is one and the same refusal, so a padding error, a wrong key and a broken tag cannot be told apart.

## `saml2-model`

The model reads an assertion only in what a signature covers, takes a peer's keys from its metadata only, and
knows no HTTP.

``` php
use Beffroi\Saml2\Model\Protocol\UnverifiedResponse;
use Beffroi\Saml2\Model\SamlLoader;
use Beffroi\Saml2\Model\Validation\{ExpectedResponse, ResponseValidator, TimeBounds};

$loader = SamlLoader::create();                              // one loader, one ID space for SAML, ds: and xenc:
$response = UnverifiedResponse::of($loader->load($bytes));   // the bytes a binding decoded
$idp = $peers->identityProvider($response->issuer);          // the unverified issuer chooses the peer, nothing else

$accepted = new ResponseValidator($loader, $clock, $replayGuard, new TimeBounds())->validate(
    $response,
    $idp,
    ExpectedResponse::toRequest($requestId, 'https://sp.example.com/saml/acs', 'https://sp.example.com/saml'),
);
$accepted->assertion->nameId->value;                         // read from the verified document only
```

`validate()` refuses with an exception that names its rule, `SignatureRequired`, `AudienceMismatch`,
`OutsideValidityWindow`, `Replayed` and the others. The other messages of the two profiles have their writer
and their validator: `AuthnRequestWriter` and `AuthnRequestValidator`, `ResponseWriter`,
`LogoutRequestWriter` and `LogoutRequestValidator`, `LogoutResponseWriter` and `LogoutResponseValidator`, and
`MetadataReader` and `MetadataWriter` for the metadata.

| | The model guarantees |
|---|---|
| M-1 | What is read is what was verified, or what was decrypted from a ciphertext that was |
| M-2 | Every assertion is covered by a signature, its own or the response's, and every signature present verifies |
| M-3 | A peer's keys come from its metadata; the `KeyInfo` of a message is never read |
| M-4 | One assertion per response, found as a direct child; one subject, one bearer confirmation |
| M-5 | The order and cardinality of the schema are code; a closed vocabulary refuses what it does not know |
| M-6 | One lexical form per value: UTC times, booleans never cast, absolute URIs of 1024 characters at most |
| M-7 | Time comes from a PSR-20 clock, and every window has a bounded skew |
| M-8 | `Issuer`, `Audience`, `Recipient` and `Destination` are compared byte for byte |
| M-9 | An assertion goes only to an assertion consumer service the metadata list |
| M-10 | `InResponseTo` answers the request the consumer names, or is absent when it accepts an unsolicited response |
| M-11 | An assertion, and a logout message, is accepted once |
| M-12 | A `NameID` follows the rules of its format, read whole |
| M-13 | A failure status, an unknown condition or an unsupported element is a refusal |
| M-14 | One loader and one space of identifiers for SAML, XML Signature and XML Encryption |
| M-15 | What it writes, it reads back under the same rules |
| M-16 | A refusal names its rule and never carries a value of the message |
| M-17 | Every count and length is bounded, and checked before anything iterates |
| M-18 | The consumer is told whether the assertion arrived encrypted |

**Two ports.** The clock is PSR-20's `ClockInterface`. The replay port is one method, implemented over a store
every worker of the deployment shares, atomically: a store per process forgets across workers.

``` php
namespace Beffroi\Saml2\Model\Port;

interface ReplayGuardInterface
{
    /** true when the pair was new and is now remembered until $expiresAt, false when it was seen */
    public function remember(string $issuer, string $id, \DateTimeImmutable $expiresAt): bool;
}
```

## `saml2-bindings`

The two browser bindings, on strings and arrays: a query string or the fields of a form decoded into the
document the model reads, and a message the model writes turned into a URL or a form. It reads no SAML
element itself; which message it expects is the method that is called.

``` php
use Beffroi\Saml2\Bindings\RedirectReceiver;
use Beffroi\Saml2\Model\SamlLoader;
use Beffroi\Saml2\Model\Validation\AuthnRequestValidator;

$loader = SamlLoader::create();
$received = new RedirectReceiver($loader)->authnRequest($queryString);   // the raw QUERY_STRING, as it arrived
$accepted = $received->validate(
    new AuthnRequestValidator($loader, $clock),
    $peers->serviceProvider($received->request->issuer),
    $self,
    'https://idp.example.com/saml/sso',                                  // the endpoint, from configuration
);
$received->relayState;                                                  // opaque, echoed in the answer
```

| | The bindings guarantee |
|---|---|
| B-1 | One message parameter, and every parameter at most once, under its literal name |
| B-2 | The HTTP-Redirect signature is verified over `SAMLRequest` or `SAMLResponse`, `RelayState` and `SigAlg`, in that order, as received |
| B-3 | `Signature` and `SigAlg` go together, `SigAlg` on the closed list of `xml-security`, SHA-1 and DSA refused |
| B-4 | The keys are those of the peer's metadata |
| B-5 | The model hears that the binding authenticated a message only from this package, after the signature held over the very input the message was decoded from |
| B-6 | No XML signature travels over HTTP-Redirect |
| B-7 | Every input is bounded before it is decoded, and DEFLATE while it inflates |
| B-8 | One lexical form: strict percent-encoding, canonical base64, raw DEFLATE complete and alone |
| B-9 | `RelayState` is opaque, 1024 bytes at most, never empty, and never given to the model |
| B-10 | What arrived is loaded as it arrived; what is sent is serialized once |
| B-11 | A refusal names its rule and never carries a value of the input |
| B-12 | No response over HTTP-Redirect, and every logout message sent is signed |
| B-13 | No HTTP object, no superglobal, no header, no HTML |

Two deviations from SAML Bindings are deliberate, and neither is a switch: RSA-SHA1 and DSA-SHA1, which
§3.4.4.1 requires, are refused; and a `RelayState` of up to 1024 bytes is read and sent where §3.4.3 and
§3.5.3 say 80, since real service providers send longer ones.

**What the application holds.** The raw query string, never one a framework normalised; the fields of an
`application/x-www-form-urlencoded` body, any other content type refused before the call; the URL of its own
endpoint from its configuration, never rebuilt from the `Host` of the request; the `RelayState` it draws, an
unguessable reference to state it keeps; and the page that posts a form, every value escaped for HTML and the
script that submits it allowed by the content security policy.

## What a consumer never calls

Each package is held by PHPStan rules of its own, kept in the monorepo beside its tests, which its consumers
are asked to copy: the DOM classes, XPath, SimpleXML, `XMLReader` and `XMLWriter` outside the loader, the
flags of libxml that load a DTD or expand an entity, `getElementById()`, the weak generators of randomness, a
loose comparison and a cast to `bool`. Above them, `beffroi/saml` never calls the method by which the bindings tell the model a signature
held, nor Reflection, `Closure::bind()` or the unserializer, any of which would let a message received over
the binding be paired with a signature verified over another input. Its analysis proves each ban with a
fixture, one line per banned form, so a rule that stops firing turns the build red.

The specification of each package is in its directory of the monorepo,
[`beffroi-auth/beffroi`](https://github.com/beffroi-auth/beffroi), and each is published read only as a
repository of its own.
