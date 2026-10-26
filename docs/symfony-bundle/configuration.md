---
title: Configuration
description: "The tree under `beffroi`, section by section: what each one decides, when a deployment needs it, and what leaving it out means."
---

# Configuration

The bundle reads one tree under `beffroi`, and each key at its root is a section with a class of its own in
the bundle. Two sections are required, `tenant` and `keys`. Every other one has defaults a provider runs on,
and a capability whose section names nothing is either served with those defaults or not served at all: a
tenant that names no registration `mode` has no registration endpoint, in its discovery document as on the
wire. This page goes through the sections in the order of the tree; [the reference](../reference/configuration.md)
lists every option with its type, its default and its bounds.

The smallest configuration names the issuer and the key management client the private keys are sealed with:

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tenant:
        issuer: '%env(BEFFROI_ISSUER)%'
    keys:
        kms: default
        key_id: '%env(BEFFROI_KMS_KEY_ID)%'
```

## The sections

| Section | What it decides | Left out |
|---|---|---|
| [`tenant`](#tenant) | The issuer, the name and the look of the tenant, and its `acr` vocabulary | Required |
| [`keys`](#keys) | The client that seals the keys, where they are kept, and how they rotate | Required |
| [`webauthn`](#webauthn) | Where the FIDO metadata are kept | `var/webauthn` of the project |
| [`mutual_tls`](#mutual_tls) | The host that asks a client for its certificate | No alias announced |
| [`tokens`](#tokens) | How long everything the provider issues stands | The defaults, short |
| [`load`](#load) | The request budget of an address and of a client | 2400 and 1200 a minute |
| [`journal`](#journal) | How long an act is kept | 180 days |
| [`history`](#history) | How long a change of a claim is kept | 180 days |
| [`geoip`](#geoip) | The databases that place an address, and the key they are downloaded under | An address, no place |
| [`passwords`](#passwords) | The list of compromised passwords a new one is compared with | No list asked |
| [`interaction`](#interaction) | How the `login_hint` of an authorization request is read | As a `sub` |
| [`back_channel_logout`](#back_channel_logout) | How long a notification to a third party is tried | Six retries, 235 seconds in all |
| [`backchannel_authentication`](#backchannel_authentication) | How the `login_hint` of a backchannel request is read | As a `sub` |
| [`web_push`](#web_push) | Whether the provider reaches people through their browsers | No push |
| [`client_authentication`](#client_authentication) | What a client assertion and a published key set are held to | The defaults |
| [`request_objects`](#request_objects) | What a request object and its `request_uri` are held to | The defaults |
| [`dpop`](#dpop) | What a proof of possession is held to | No nonce asked |
| [`trusted_issuers`](#trusted_issuers) | The issuers of the JWT bearer grant | The grant serves nobody |
| [`clients`](#clients) | The clients the deployment declares | No client |
| [`client_registration`](#client_registration) | Whether and how a client registers itself | No registration endpoint |
| [`saml`](#saml) | The SAML roles of the tenant and its peers | No SAML |

## When a mistake is caught

**When the container is built**, at `cache:clear`, at `cache:warmup`, or at the first boot of a process that
finds no compiled container. The tree is checked there: an unknown key at any level, a value of the wrong
type, a number written outside its bounds, a required option missing, a value outside its list. So are the
rules the tree reads between options, a sliding refresh lifetime longer than the absolute one, a SAML
`cache_duration` that is not shorter than the SAML staging delay, a SAML peer declared for a role that is off;
the name of the key management client; and every SAML declaration, the claims it names included. A deployment
pipeline that warms its cache stops there. A SAML declaration that holds an environment variable is checked at
its first use instead.

**When the provider first reads a declaration.** What only the wiring can answer is checked against the
wiring, the first time the provider builds the object: the tenant, each declared client, each trusted issuer,
each authority of software statements, the default scope of registrations. A refusal names the option and,
where the wiring decides, the names it is wired with, so a misspelt algorithm is answered with the algorithms
that exist. What reads a declaration first is what meets its refusal:

- `bin/console beffroi:tenant:synchronize` builds the tenant;
- `bin/console beffroi:client:list`, once the tenant is synchronized, reads every declared client, and with one
  client declared at least, every trusted issuer as well;
- the discovery document, `/.well-known/openid-configuration` under the issuer, builds all of it once the tenant
  is synchronized: the tenant, the declared clients, the trusted issuers, and the policy of registration, its
  authorities of software statements and its default scope included, which no command of the bundle builds.

A deployment that runs `beffroi:tenant:synchronize` and then reads the discovery document has met every one of
these refusals before a client asks anything. Otherwise the first request that needs the object meets it, and the policy of registration is
also built by the timed step that removes the clients nobody uses.

**No option does it wrong.** The tree holds no `insecure_*` key and no compatibility switch. An exception a
specification admits is named and bounded: `requires_pkce: false` exempts one confidential client, and is
refused for a public one. [Secure by default](../the-project/secure-by-default.md) is the rule.

## `tenant`

Who the provider is, and required. `issuer` is the identifier every token carries as `iss` and the URL every
endpoint is served under: the routes of the bundle are imported under its path, which the provider checks at
the first request. `slug` names the tenant for good: its identifier is derived from it, and renaming it is
creating another tenant. `name` and `look` are what the pages show of the tenant, `self_served_claims` what its
people may change of themselves, and `authentication_classes` the `acr` it answers with.

The logo is loaded by the browser of the visitor, under the `Content-Security-Policy` the application sends.
The consent page adds the origin of the logo to its `img-src`, and no other page does: a logo served from
another origin than the pages is named in the `img-src` of the application's own policy, as
[the standalone application](../application/configuration.md) says of its own.

The row of the tenant follows the configuration through `bin/console beffroi:tenant:synchronize`, which is
safe to run at every deployment.

[:beffroi-arrow-right: Tenants](../core/tenants.md)

## `keys`

Where the keys of the tenant are sealed and kept, and required. The bundle builds no key management client:
`kms` names one declared under `key_management.clients`, a DSN or a composite of several, and `key_id` names
the key of that client the keys are sealed under, `{tenant}` standing for the slug.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    keys:
        kms: default
        key_id: 'beffroi-{tenant}'
        storage: '%kernel.project_dir%/var/keys'
```

`storage` is the directory of the sealed key files and of the pairwise salt of the tenant, sealed the same
way. The salt is drawn on first use and never again, and every pairwise subject of the tenant is computed from
it, so the directory is part of what a deployment backs up.

The three other options time the rotation of every key but the SAML keys. A relying party keeps the JWK Set
for `jwks_max_age`, five minutes. A new key is published for `staging_delay` before it signs, by default
`jwks_max_age` plus the sixty seconds after which Symfony's `oidc_login` reads the set again for a `kid` it
does not hold. A key works for `age`, ninety days, before the timed step stages a successor behind it, which is
inside the one to three years NIST SP 800-57 Part 1 Rev. 5 §5.3.6 gives a private signature key.

[:beffroi-arrow-right: Key management](key-management.md) and [keys](../core/keys.md)

## `webauthn`

Where the FIDO metadata a passkey's attestation is checked against are kept: what
`beffroi:webauthn:mds-refresh` downloads and `beffroi:webauthn:mds-import` stores. Left out, the directory is
`var/webauthn` of the project. A passkey enrols while it is empty.

[:beffroi-arrow-right: Passkeys](../core/credentials/passkeys.md)

## `mutual_tls`

For a deployment whose clients authenticate with a certificate (RFC 8705) on a host whose TLS listener asks
for one. Named, the discovery document announces every endpoint again under that host, in
`mtls_endpoint_aliases`. Left out, or empty, no alias is announced, which is what a deployment serving one host
does.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    mutual_tls:
        origin: 'https://mtls.op.example.com'
```

[:beffroi-arrow-right: Mutual TLS](../oidc/sender-constrained/mutual-tls.md)

## `tokens`

How long the codes, requests and tokens the provider issues stand, in seconds. Left out, every lifetime is
short: a minute for an authorization code and a pushed request, ten minutes for an access token and an ID
token, thirty days of sliding life and ninety in all for a refresh token. The tree bounds them: an
authorization code and a `request_uri` live ten minutes at most (RFC 6749 §4.1.2, RFC 9126 §2.2), a device code
thirty minutes, a backchannel request an hour, an interval between two polls thirty seconds, and a refresh
token never slides past the absolute lifetime of its family.

The lifetimes of what a key signs are also how long that key stays published once another key takes over from
it, so that a token still in use verifies: ten minutes for a signing key with the defaults. A longer
`access_token_ttl` keeps a retiring key in the JWK Set for longer.

[:beffroi-arrow-right: Tokens](../oidc/tokens/index.md)

## `load`

Every request is counted against two budgets, and the section sets their numbers, never whether they exist.
The first counts the address of the client, on every route of the bundle and before anything is verified; the
second counts a client of a tenant once it has authenticated. A request over a budget is answered `429` with a
`Retry-After` header.

The address is the one Symfony reads behind the trusted proxies of the application, so a deployment behind a
load balancer declares the balancer as a trusted proxy, or every request counts against the address of the
balancer. The counts live in the `beffroi.load` cache pool, on `cache.app` unless the deployment points the
pool at a store its processes share. A number too low on `/token` or on `/jwks` refuses the deployment's own
clients, so a deployment sets them from what its own clients send.

## `journal`

How long an act of the journal is kept before the timed step forgets it: 180 days unless the section says
otherwise. What a client was given of a person in an act is forgotten with that act. Nothing turns the journal
on or off.

## `history`

How long a change a person made to their claims is kept before the timed step forgets it: 180 days unless the
section says otherwise, the default of the journal too, a change and the act that announced it being two
halves of one answer.

## `geoip`

Where the GeoLite2 databases that place the address of a request are kept, and the licence key of the MaxMind
account they are downloaded under. MaxMind publishes them under its own licence, so nothing is shipped, and a
deployment that names no key downloads nothing: every flow is served, and a provenance says an address and no
place.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    geoip:
        license_key: '%env(GEOIP_LICENSE_KEY)%'
```

A weekly timed step downloads them, and `bin/console beffroi:geoip:refresh` does it at once.

## `passwords`

The list of compromised passwords a password is compared with before it is written (NIST SP 800-63B
§3.1.1.2). How long a password has to be and how hard it is to guess are rules of the core, and no option
lowers them. Left out, no list is asked and nothing of a password leaves the deployment.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    passwords:
        breached:
            endpoint: 'https://api.pwnedpasswords.com/range/'
```

Named, the endpoint receives the first five hexadecimal characters of the SHA-1 of a password, and the rest is
compared locally. A password the list counts is refused, and so is one the list could not be asked about,
within `timeout`, two seconds. A password already set is looked up again after a login that used it, on the
asynchronous lane.

[:beffroi-arrow-right: Passwords](../core/credentials/passwords.md)

## `interaction`

How the `login_hint` of an authorization request is read (OIDC Core §3.1.2.1): `sub`, the subject the
provider issued to that client, by default; `username`, the name a person signs in with; or `none`, for a
deployment that tags a reading of its own `beffroi.oidc.login_hint`. It is read one way and never searched,
and the login page offers the name of the person it names.

[:beffroi-arrow-right: Interactions](../oidc/interactions.md)

## `back_channel_logout`

How a logout token is posted to a client that registered a `backchannel_logout_uri` (Back-Channel Logout 1.0
§2.5): five seconds an attempt, then six retries, two seconds after the first failure and three times longer
each time, a minute at most. The retry schedule is the one of every notification the provider carries to a
third party, on the `async_notifications` transport the bundle configures: the logout tokens, the
notifications of the backchannel authentication flow, and the pushes that tell a person something waits for
them.

The schedule is also the `exp` of a logout token, 235 seconds with the defaults, and a retiring signing key
stays published that long at least, so that the provider stops trying when what it sends stops being
verifiable. An application that routes the notifications to a transport of its own keeps that agreement only
if the transport retries with the policy of the bundle; `bin/console beffroi:doctor` says whether it does.

[:beffroi-arrow-right: Logout](../oidc/logout.md) and [Messenger](messenger.md)

## `backchannel_authentication`

How the `login_hint` of a backchannel authentication request is read (CIBA Core §7.1), under the three readings
of `interaction`, `none` being for a deployment that tags its own `beffroi.oidc.ciba_user_hint`, and how long
one call to a client in `ping` mode may take. Nothing here opens the flow: a client takes part in it by
registering its grant and a delivery mode.

[:beffroi-arrow-right: Backchannel authentication](../oidc/grants/backchannel-authentication.md)

## `web_push`

Whether the provider reaches people through the push services of their browsers (RFC 8030). Naming a
`subject` turns it on: a `mailto:` or `https:` URI at which a push service can reach the operator (RFC 8292
§2.1). Left out, nothing of it is wired, no push leaves the deployment, and the page where a browser would
subscribe says so.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    web_push:
        subject: 'mailto:operator@example.com'
```

The push is signed with the application server key of the tenant, drawn like every other key of the tenant:

``` bash
bin/console beffroi:keys:generate --algorithm=VAPID
```

[:beffroi-arrow-right: Web push](web-push.md)

## `client_authentication`

What a client assertion is held to (RFC 7523 §3), how far ahead its `exp` may be and how much clock it is
allowed, and what one read of a `jwks_uri` may cost: its timeout, its size, how long its keys are kept and how
often an unknown `kid` may read it again. The bounds of a read are those of every published key set the
provider reads, the clients' and the trusted issuers'. Which methods a client may authenticate with is the
wiring and its registration, and nothing of this section.

[:beffroi-arrow-right: Client authentication](../oidc/client-authentication.md)

## `request_objects`

What a request object is held to (RFC 9101 §4), how long it may stand and how much clock it is allowed, and
what one read of a `request_uri` may cost while the browser of a person waits on it. Which algorithm verifies
an object is the registration of the client.

[:beffroi-arrow-right: Request objects](../oidc/request-objects.md)

## `dpop`

What a proof of possession is held to (RFC 9449): its age, the clock allowed, and whether it carries a nonce of
the provider (RFC 9449 §8). A client that sends no proof is not concerned.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    dpop:
        nonce:
            required: true
```

`nonce.required` decides which class the container wires, so it is written as `true` or `false` in the file.

[:beffroi-arrow-right: DPoP](../oidc/sender-constrained/dpop.md)

## `trusted_issuers`

The issuers whose assertions the tenant accepts as an authorization grant (RFC 7523 §2.1). Whoever holds the
signing key of one of them can name a user of the tenant and be answered with an access token, so each one is
declared whole: its keys, the algorithms it signs with, the clients that may present its assertions, the
source of the identities it names and the scopes it is trusted for. Left out, the grant serves nobody.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    trusted_issuers:
        'https://workforce.example.com':
            jwks_uri: 'https://workforce.example.com/jwks'
            signing_algorithms: ['ES256']
            clients: ['job-runner']
            identity_provider: workforce
            trusted_scopes: ['invoices.read']
```

The `sub` of an assertion names a user of the tenant only through a linked identity of the source
`identity_provider` names, and no user is ever created from an assertion.

[:beffroi-arrow-right: The JWT bearer grant](../oidc/grants/jwt-bearer.md)

## `clients`

The clients the deployment declares, keyed by `client_id`, each read like a registration of RFC 7591 §2. A
client the configuration does not declare exists only if it registered itself, at the endpoint
`client_registration` opens. A declared client that writes nothing takes the browser flow and its renewal, the
scopes `openid profile email`, and the first wired method of authentication, `client_secret_basic`, which needs
a secret.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        my-application:
            client_name: 'My application'
            secret: '%env(MY_APPLICATION_SECRET)%'
            redirect_uris: ['https://app.example.com/oidc/callback']
            post_logout_redirect_uris: ['https://app.example.com/']
            scope: 'openid profile email offline_access'
        reporting:
            secret: '%env(REPORTING_SECRET)%'
            grant_types: ['client_credentials']
            scope: 'invoices.read'
            resources: ['https://api.example.com/']
```

The options of a client hold together or the client is refused, naming the rule:

- the method of authentication decides what else is registered: a secret for `client_secret_basic`,
  `client_secret_post` and `client_secret_jwt`, and for no other; keys in `jwks` or behind `jwks_uri` for
  `private_key_jwt` and `self_signed_tls_client_auth`; one name of the certificate for `tls_client_auth`;
- a client registered for `authorization_code` registers a redirect URI at least, and a client registered for
  no grant that sends the browser back registers none;
- a public client, `token_endpoint_auth_method: none`, keeps PKCE, writes plain `http` redirect URIs on
  `127.0.0.1` or `[::1]` only, and is refused `client_credentials`;
- an encrypted response is named with both its algorithms, and the client publishes a key to encrypt to.

The secret of a declared client belongs in the environment, as the example reads it, and it is hashed when the
client is first read, except for `client_secret_jwt`, which needs the secret itself.

[:beffroi-arrow-right: Clients](../oidc/clients.md) and [your first client](../getting-started/your-first-client.md)

## `client_registration`

Whether a client nobody declared may register itself (RFC 7591), and on what authority. Left out, the tenant
has no registration endpoint: none in its discovery document, and `404` on the wire. A `mode` opens it:
`initial_access_token`, a token the tenant issues, limits and revokes; `software_statement`, a statement signed
by an authority the tenant pins under `statement_issuers`; or `open`, no credential at all, for a tenant with no
real user.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    client_registration:
        mode: initial_access_token
```

``` bash
bin/console beffroi:client:token:issue 'Partner integration' --registrations=5 --days=7
```

The name says later which integration a token was for. Without the options, a token registers one client and
is worth thirty days; its value is printed once, and the provider keeps only its digest.

A client that registered itself is deleted after ninety days without use, or after seven days when it was never
used. The rest of the section bounds the read of a `sector_identifier_uri` and the software statements, names
the scopes of a client that asks for none, and, for a tenant whose clients send no `code_challenge`, exempts
its confidential clients from PKCE, never a public one.

[:beffroi-arrow-right: Dynamic registration](../oidc/dynamic-registration.md)

## `saml`

The SAML roles of the tenant, each off unless the section turns it on, and the peers of each. A role that is off
wires nothing and answers `404` where its metadata would be, and the peers of a role are refused while it is
off.

| Key | What it is | The page |
|---|---|---|
| `identity_provider` | The tenant as an identity provider, and the rotation of every SAML key | [The identity provider](../saml/identity-provider.md) |
| `service_providers` | The applications that sign their users in through it | [Service providers](../saml/service-providers.md) |
| `service_provider` | The tenant as a service provider to identity providers upstream of it | [Upstream identity providers](../saml/upstream-identity-providers.md) |
| `identity_providers` | The identity providers upstream of it, and the e-mail domains each answers for | [Upstream identity providers](../saml/upstream-identity-providers.md) |

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    saml:
        identity_provider: true
```

Writing a role as a block turns it on as well, unless the block says `enabled: false`.
