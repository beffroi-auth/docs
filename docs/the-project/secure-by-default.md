---
title: Secure by default
description: The protections Beffroi applies with no option to turn them off, and the few exceptions, each one named and bounded.
---

# Secure by default

A provider that can be configured insecurely will be, and the person who pays for it is never the one who
wrote the option. So Beffroi has no option to do it wrong: the protections below are properties of the
code. There is no `insecure_` setting, no compatibility mode, and no global switch.

## What is always on

| Rule | Why |
|---|---|
| PKCE is mandatory, `S256` only | `plain` protects nothing against an attacker who reads the request. A code intercepted without the verifier is useless |
| No implicit flow | Tokens in a URL fragment end up in history, logs and referrers |
| No resource owner password credentials grant | It teaches applications to collect passwords, which is the habit the protocol exists to break |
| Redirect URIs are compared exactly | Prefix and wildcard matching is how an open redirector becomes a token leak |
| `iss` is in every authorization response | A client must be able to tell which provider answered. RFC 9207 |
| Access tokens are `at+jwt` or opaque references, never an ambiguous shape | A resource server must know what it is validating. RFC 9068 |
| No redirect is followed outbound | Fetching a client's metadata or keys must not become a request to an address the client chose |
| No boolean from a third party is ever cast | A missing claim and a false claim are not the same thing, and `(bool)` makes them one |
| Every secret string comes from a cryptographic source, every secret comparison is constant time | |
| A password is compared against a list of compromised values before it is written | A password can be long, varied and still known to everybody. NIST SP 800-63B §5.1.1.2 asks for the list, and what the list holds is refused rather than warned about |
| A page that adds or takes away a way in asks for the proof again | A session outlives the moment it was opened, which is right for a page that shows what the account holds and wrong for the gesture somebody else would lock its owner out with |
| What leaves the process on a transport leaves sealed | What a column seals, a queue may not carry in clear: the body of every message is sealed to the tenant, so a broker, a failure table and a backup of either are worth nothing without the key management service |

## Where an exception exists

An exception is named, bounded and written down, never a switch in a configuration file. Two examples of
the shape they take:

- **PKCE can be waived by the registration policy**, not by the client. A tenant that must serve a client
  which cannot do PKCE says so in its own policy, for that client, and the waiver is visible where clients
  are read.
- **Dynamic client registration is controlled.** The endpoint exists, and the tenant decides the mode it
  runs in: who may register, what an initial access token buys, and which authority may vouch for a piece
  of software it did not issue.

## Keys and personal data

Signing keys and the data keys that protect personal data are held by a key management service, never by
the application: the application asks for an operation and never holds the master key. Keys rotate
without a restart and without breaking a token already in flight.

Personal data is sealed in its column, with blind indexes for the lookups that must still work. A dump of
the database is searched byte by byte by a test that fails when it finds a value it should not, and the
same search finds a value the schema declares readable, so a green run is a search that was looking.

A key works for an age and no longer: a successor is staged behind it without anybody asking, and
`beffroi:keys:list --check` fails on a key that has worked past that age with nothing staged behind it, so
the question is answered in a deployment pipeline rather than at the next rotation.

The one file in which everything the provider holds of a person stands in clear at once is the archive
that person asks for, and it is held by three rules rather than by a setting: it is sealed where it sits
like every other column, it expires a week after it was asked for, and that week is a figure in the code.
A person who wants it to leave under a passphrase of their own choosing says so when they download it, and
the floor on the length of that passphrase is refused rather than warned about, since what stands between
that file and whoever took it is the length of what was typed.

[:beffroi-arrow-right: Keys](../core/keys.md) and [personal data](../core/personal-data.md).

## What a deployment answers with

Headers are shared by a rule: the bundle writes what belongs to a page it builds, the application writes
what belongs to a deployment, and neither writes a header the other does. A header written twice is not
replaced, it collides: two content policies intersect, two `Access-Control-Allow-Origin` are invalid and
the response is rejected.

What [the standalone application](../application/index.md) answers with is therefore named where that
application is configured and nowhere else:
`nosniff` and `DENY` everywhere, `Referrer-Policy: no-referrer`, HSTS for a year with the subdomains and
the preload list, a permissions policy whose whole set is written down with two entries open to this
origin alone, the two a passkey ceremony needs, and a content policy that starts at `default-src 'none'`
and then names one directive per kind of thing a page of this deployment loads. Neither `unsafe-inline`
nor `unsafe-eval` is one of them.

The one header of that configuration that opens anything is CORS, so it is cut to what needs it: the six
endpoints a public client running in a page calls, which are discovery, the JWK Set, the token endpoint,
UserInfo, revocation and the pushed authorization request. Credentials are never allowed, which is what
makes the wildcard correct: a browser refuses the two together, and the session of this provider is read
on pages of the interaction plane, none of which is on that list.
