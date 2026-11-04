---
title: Configuration tree
description: "The tree under `beffroi` the application writes, section by section: what each one decides, the variables a deployment sets it with, and what the image holds."
---

# Configuration tree

The application reads one tree under `beffroi`, its own `config/packages/beffroi.yaml`, and each key at its
root is a section with a class of its own in `src/Configuration/`. The file reads each value a deployment
chooses from an environment variable, which [the configuration](configuration.md) lists, and writes in itself
only what is the same for every deployment of the image, as [what the files
say](configuration.md#what-the-files-say) details. A deployment of the image writes no part of the tree: it
sets the variables.

Two sections are required, `tenant` and `keys`. Every other one has defaults, and a capability is served with
the values the image holds or not served at all: `.env` leaves `BEFFROI_REGISTRATION_MODE` empty, so the
tenant of the image has no registration endpoint, in its discovery document as on the wire, until a deployment
names a mode. This page goes through the sections in the order of the tree, its examples writing each section
as the application's file writes it and its prose naming the variables; [the
reference](../reference/configuration.md) lists every option with its variable, its value in the image, its
type and its bounds.

The two required sections name the issuer and the key management client the private keys are sealed with,
`op`, and the file reads the issuer and the master key from the environment:

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tenant:
        issuer: '%env(BEFFROI_ISSUER)%'
    keys:
        kms: op
        key_id: '%env(BEFFROI_KMS_KEY_ID)%'
```

## The sections

| Section | What it decides | In the image |
|---|---|---|
| [`tenant`](#tenant) | The issuer, the name and the look of the tenant, the claims its people change, its `acr` vocabulary and the scopes of its APIs | Required. `BEFFROI_ISSUER`, `BEFFROI_TENANT_SLUG` and the `BEFFROI_TENANT_*` variables |
| [`keys`](#keys) | The client that seals the keys, where they are kept, what binds the data keys, and how keys rotate | Required. `op` and `var/keys` written in the file, `BEFFROI_KMS_KEY_ID`, `BEFFROI_DATA_KEY_SECRETS` and three variables of rotation |
| [`webauthn`](#webauthn) | Where the FIDO metadata are kept | `var/webauthn` written in the file, no variable |
| [`mutual_tls`](#mutual_tls) | The host that asks a client for its certificate | `BEFFROI_MTLS_ORIGIN`, empty: no alias announced |
| [`tokens`](#tokens) | How long everything the provider issues stands | Eleven variables, short lifetimes |
| [`load`](#load) | The request budget of an address and of a client | Four `BEFFROI_LOAD_*` variables: 2400 and 1200 a minute |
| [`journal`](#journal) | How long an act is kept | `BEFFROI_JOURNAL_RETENTION`: 180 days |
| [`history`](#history) | How long a change of a claim is kept | `BEFFROI_HISTORY_RETENTION`: 180 days |
| [`geoip`](#geoip) | The databases that place an address, and the key they are downloaded under | `GEOIP_LICENSE_KEY`, empty: an address, no place |
| [`passwords`](#passwords) | The list of compromised passwords a new one is compared with | `BEFFROI_BREACHED_PASSWORDS_ENDPOINT`, empty: no list asked |
| [`interaction`](#interaction) | How the `login_hint` of an authorization request is read | `BEFFROI_INTERACTION_LOGIN_HINT`: as a `sub` |
| [`back_channel_logout`](#back_channel_logout) | How long a notification to a third party is tried | Five `BEFFROI_BACK_CHANNEL_LOGOUT_*` variables: six retries, 235 seconds in all |
| [`backchannel_authentication`](#backchannel_authentication) | How the `login_hint` of a backchannel request is read, and how long a call to a client may take | `BEFFROI_BACKCHANNEL_AUTHENTICATION_LOGIN_HINT`: as a `sub`; `BEFFROI_CLIENT_NOTIFICATION_TIMEOUT`: 3 seconds |
| [`web_push`](#web_push) | Whether the provider reaches people through their browsers | `BEFFROI_WEB_PUSH_SUBJECT`: on, with the contact of the development stack |
| [`client_authentication`](#client_authentication) | What a client assertion and a published key set are held to | `BEFFROI_CLIENT_ASSERTION_*` and `BEFFROI_JWKS_URI_*` |
| [`request_objects`](#request_objects) | What a request object and its `request_uri` are held to | `BEFFROI_REQUEST_OBJECT_*` |
| [`dpop`](#dpop) | What a proof of possession is held to | `BEFFROI_DPOP_*`: no nonce asked |
| [`trusted_issuers`](#trusted_issuers) | The issuers of the JWT bearer grant | `BEFFROI_TRUSTED_ISSUERS`, `{}`. The grant issues no token on the image, whatever this names |
| [`clients`](#clients) | The clients a file of the application declares | Empty, no variable: a client registers itself |
| [`self_client`](#self_client) | The application as a client of its own provider | Not written, no variable: the application is no client |
| [`client_registration`](#client_registration) | Whether and how a client registers itself | `BEFFROI_REGISTRATION_*`, an empty mode: no registration endpoint |
| [`saml`](#saml) | The SAML roles of the tenant, the peers of each and the SAML keys | `BEFFROI_SAML_*`: an identity provider, no peer |

## When a mistake is caught

**When the container is compiled**, which for the image is when the image is built. The tree is checked
there: an unknown key at any level, a value of the wrong type, a number written outside its bounds, a required
option missing, a value outside its list, the rules the tree reads between options, and the name of the key
management client. What it checks of the image is the application's file, once: every value a deployment
chooses is a variable, which stands for a value only once a process runs.

**When the container builds the service a value reaches.** A value a variable carries is held then to the
bounds the tree sets for its option and to the rules between options, a sliding refresh lifetime longer than
the absolute one, a SAML `cache_duration` that is not shorter than the SAML staging delay; a list a variable
carries is held to the rules of the tree as a list written in the file is. The first request or command that
needs a value refuses it out of bounds, except the age of a key, `keys.age`, which the timed step of the key
lifecycle refuses at its first tick when it is not longer than the retirement window of its use, and a change
of variable asks for a restart of the processes, not for a new image.

**When the provider first reads a declaration.** What only the wiring can answer is checked against the
wiring, the first time the provider builds the object: the tenant, the scopes of its APIs, each trusted
issuer, each authority of software statements, the default scope of registrations, and each SAML peer, the
claims it names included. A refusal names the option and, where the wiring decides, the names it is wired
with, so a misspelt algorithm is answered with the algorithms that exist. What reads a declaration first is
what meets its refusal:

- `bin/console beffroi:tenant:synchronize` builds the tenant;
- the discovery document, `/.well-known/openid-configuration` under the issuer, builds the rest once the
  tenant is synchronized: the scopes the tenant hands out, the trusted issuers, and the policy of
  registration, its authorities of software statements and its default scope included, which no `beffroi:`
  command builds;
- `bin/console beffroi:saml:service-provider:refresh` and `bin/console beffroi:saml:identity-provider:refresh`
  build the peers of each SAML role, as the hourly refresh of their metadata does.

A deployment that runs `beffroi:tenant:synchronize`, reads the discovery document and refreshes the metadata
of its SAML peers has met every one of these refusals before a client asks anything. Otherwise the first
request that needs the object meets it, and the policy of registration is also built by the timed step that
removes the clients nobody uses.

**No option does it wrong.** The tree holds no `insecure_*` key and no compatibility switch. An exception a
specification admits is named and bounded: `requires_pkce: false` exempts one confidential client, and is
refused for a public one. It is a member of the deployment, which no client of the image carries: [what the
image does not set](../oidc/clients.md#what-the-image-does-not-set). [Secure by
default](../the-project/secure-by-default.md) is the rule.

## What the tree writes for the other bundles

When the container is built, `App\DependencyInjection\BeffroiExtension` prepends its part to the configuration
of the extensions the provider works with, and only of those the kernel registers. A prepended configuration
is merged first, so a key a file of the application writes itself is the one that stands: the suite of the
application writes the transports again, every lane on `sync://`, and the files the image carries write none
of these keys but the directory of the migrations, which `config/packages/doctrine_migrations.yaml` names the
same way.

| Extension | What the tree adds |
|---|---|
| `doctrine` | The DBAL types of the application, and three XML mappings, `BeffroiCore`, `BeffroiOidc` and `BeffroiSaml`, for the model of the three packages, read from `config/beffroi/doctrine/core`, `config/beffroi/doctrine/oidc` and `config/beffroi/doctrine/saml`. The types that seal a column are registered when the kernel boots |
| `doctrine_migrations` | The directory of the migrations, `migrations/`, under the namespace `DoctrineMigrations` |
| `security` | The password hasher of `App\Security\SecurityUser`, which is `App\Security\CorePasswordHasher`, the hasher of the core |
| `rate_limiter` | Two limiters, `beffroi_code_attempts` and `beffroi_password_attempts`: five attempts per user in a sliding window of one minute |
| `framework` | Eight cache pools on `cache.app`: `beffroi.client_keys`, `beffroi.issuer_keys`, `beffroi.client_assertions`, `beffroi.issuer_assertions`, `beffroi.software_statements`, `beffroi.request_objects`, `beffroi.dpop` and `beffroi.load` |
| `messenger` | The three buses, their middleware, the routing of every message, the serializer that seals a body, and the transports: the four lanes on `BEFFROI_MESSENGER_DSN`, a queue of the database per lane unless it names another, and the failure transport in the database |
| `scheduler` | `use_messenger_routing: true`, so that the recurring messages of the provider are routed by their class like every other message |

The kernel registers the extension itself: `App\Kernel` uses `App\DependencyInjection\BeffroiKernelTrait`,
which adds the extension and its compiler passes when the container is built, and, when the kernel boots,
hands the DBAL types that read the wiring back what the deployment is wired with and registers the types that
seal a column.

[:beffroi-arrow-right: Persistence](persistence.md) &nbsp; [:beffroi-arrow-right: Messenger](messenger.md)

## `tenant`

Who the provider is, and required. `issuer` is the identifier every token carries as `iss` and the URL every
endpoint is served under: the application imports its routes at the root, so its issuer is an origin with no
path, which the provider checks at the first request. `slug` names the tenant for good: its identifier is
derived from it, and renaming it is creating another tenant. `name` and `look` are what the pages show of the
tenant, `self_served_claims` what its people may change of themselves, `authentication_classes` the `acr` it
answers with, and `scopes` the scopes of the APIs it protects, which a client that registers itself may
register beside `openid`, the scopes of the claims and `offline_access`.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tenant:
        issuer: '%env(BEFFROI_ISSUER)%'
        slug: '%env(BEFFROI_TENANT_SLUG)%'
        name: '%env(default::BEFFROI_TENANT_NAME)%'
        look:
            logo_uri: '%env(default:app.tenant_logo_uri:BEFFROI_TENANT_LOGO_URI)%'
            primary_color: '%env(default::BEFFROI_TENANT_PRIMARY_COLOR)%'
            primary_content_color: '%env(default::BEFFROI_TENANT_PRIMARY_CONTENT_COLOR)%'
        self_served_claims: '%env(json:BEFFROI_TENANT_SELF_SERVED_CLAIMS)%'
        authentication_classes: '%env(json:BEFFROI_TENANT_AUTHENTICATION_CLASSES)%'
        scopes: '%env(json:BEFFROI_TENANT_SCOPES)%'
```

`default::` makes an empty variable no value at all: an empty `BEFFROI_TENANT_NAME` names the tenant after the
host of the issuer, and an empty colour is no colour. An empty `BEFFROI_TENANT_LOGO_URI` is the parameter
`app.tenant_logo_uri` of the file, the placeholder mark the image serves at `/tenant-logo.svg` under the
issuer. The three lists are JSON documents: `.env` opens the fourteen claims the application wires to the
people of the tenant, names no `acr` class, which is the default policy, and no scope of an API.

The logo is loaded by the browser of the visitor, under the `Content-Security-Policy` the application sends.
Every page that reads the tenant adds the origin of the logo to the `img-src` of that policy, so a logo served
from another origin than the pages is named in no file of the application. Its host answers
`Cross-Origin-Resource-Policy: cross-origin`, which every page but those of `/authorize`, `/login`,
`/consent`, `/logout`, `/device` and `/initiate-login`, served under `Cross-Origin-Embedder-Policy:
require-corp`, asks of an image from another origin.

The row of the tenant follows the variables through `bin/console beffroi:tenant:synchronize`, which is safe to
run at every deployment and refuses another issuer than the one the row was written with: [the
tenant](configuration.md#the-tenant) says which values it writes there.

[:beffroi-arrow-right: Tenants](../core/tenants.md)

## `keys`

Where the keys of the tenant are sealed and kept, and required. The tree builds no key management client:
`kms` names a client of `key_management.clients`, which the application declares in
`config/packages/key_management.yaml`, and `key_id` names the key of that client the keys are sealed under,
`{tenant}` standing for the slug. The application names `op`, the client it builds from `BEFFROI_KMS_DSN`, and
reads the key from `BEFFROI_KMS_KEY_ID`, `beffroi-{tenant}` for instance. `.env` leaves both variables empty,
so every deployment names them.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    keys:
        kms: op
        key_id: '%env(BEFFROI_KMS_KEY_ID)%'
        data_key_secrets: '%env(default:app.data_key_secrets:json:BEFFROI_DATA_KEY_SECRETS)%'
        storage: '%kernel.project_dir%/var/keys'
        jwks_max_age: '%env(int:BEFFROI_JWKS_MAX_AGE)%'
        staging_delay: '%env(BEFFROI_KEY_STAGING_DELAY)%'
        age: '%env(int:BEFFROI_KEY_AGE)%'
```

`storage` is the directory of the sealed key files and of the pairwise salt of the tenant, sealed the same
way, which the file writes and no variable moves. The salt is drawn on first use and never again, and every
pairwise subject of the tenant is computed from it, so the directory is part of what a deployment backs up.

`data_key_secrets` lists the secrets every data key of personal data is bound to its row under, which the
database does not hold. `BEFFROI_DATA_KEY_SECRETS` carries them as a JSON list, and while it is not set, as in
`.env`, the secret of the kernel, `APP_SECRET`, binds them alone. The first binds a new key and a key bound
under any of them opens, so a secret is replaced by writing the new one first, as [personal
data](../core/personal-data.md#rotating-the-secret-that-binds-them) says.

The three other options time the rotation of every key but the SAML keys, which [`saml`](#saml) times. A
relying party keeps the JWK Set for `jwks_max_age`, `BEFFROI_JWKS_MAX_AGE`, five minutes in `.env`. A new key
is published for `staging_delay` before it signs, and `.env` leaves `BEFFROI_KEY_STAGING_DELAY` empty, which
makes it `jwks_max_age` plus the sixty seconds after which Symfony's `oidc_login` reads the set again for a
`kid` it does not hold. A key works for `age`, `BEFFROI_KEY_AGE`, ninety days in `.env`, before the timed step
stages a successor behind it, which is inside the one to three years NIST SP 800-57 Part 1 Rev. 5 §5.3.6 gives
a private signature key.

[:beffroi-arrow-right: Key management](key-management.md) and [keys](../core/keys.md)

## `webauthn`

Where the FIDO metadata a passkey's attestation is checked against are kept: what
`beffroi:webauthn:mds-refresh` downloads and `beffroi:webauthn:mds-import` stores. The file writes
`var/webauthn` of the application, and no variable moves it. A passkey enrols while it is empty.

[:beffroi-arrow-right: Passkeys](../core/credentials/passkeys.md)

## `mutual_tls`

For a deployment whose clients authenticate with a certificate (RFC 8705) on a host whose TLS listener asks
for one. Named, the discovery document announces every endpoint again under that host, in
`mtls_endpoint_aliases`. The file reads the origin from `BEFFROI_MTLS_ORIGIN`, as
`https://mtls.op.example.com`, and `.env` leaves it empty: no alias is announced, which is what a deployment
serving one host does.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    mutual_tls:
        origin: '%env(BEFFROI_MTLS_ORIGIN)%'
```

[:beffroi-arrow-right: Mutual TLS](../oidc/sender-constrained/mutual-tls.md)

## `tokens`

How long the codes, requests and tokens the provider issues stand, in seconds, each read from a variable [the
configuration](configuration.md#keys-and-lifetimes) lists, `BEFFROI_ACCESS_TOKEN_TTL` for an access token for
instance. `.env` keeps every lifetime short: a minute for an authorization code and a pushed request, ten
minutes for an access token and an ID token, thirty days of sliding life and ninety in all for a refresh
token. The tree bounds them: an authorization code and a `request_uri` live ten minutes at most (RFC 6749
§4.1.2, RFC 9126 §2.2), a device code thirty minutes, a backchannel request an hour, an interval between two
polls thirty seconds, and a refresh token never slides past the absolute lifetime of its family.

The lifetimes of what a key signs are also how long that key stays published once another key takes over from
it, so that a token still in use verifies: ten minutes for a signing key with the values of `.env`. A longer
`BEFFROI_ACCESS_TOKEN_TTL` keeps a retiring key in the JWK Set for longer.

[:beffroi-arrow-right: Tokens](../oidc/tokens/index.md)

## `load`

Every request is counted against two budgets, and the section sets their numbers, never whether they exist.
The first counts the address of the client, on every route of the two planes and before anything is verified;
the second counts a client of a tenant once it has authenticated. A request over a budget is answered `429`
with a `Retry-After` header. The file reads the four numbers from `BEFFROI_LOAD_ORIGIN_LIMIT`,
`BEFFROI_LOAD_ORIGIN_INTERVAL`, `BEFFROI_LOAD_CLIENT_LIMIT` and `BEFFROI_LOAD_CLIENT_INTERVAL`, which `.env`
sets to 2400 requests a minute from an address and 1200 from a client.

The address is the one Symfony reads behind the trusted proxies, so a deployment behind a load balancer names
the balancer in `SYMFONY_TRUSTED_PROXIES`, or every request counts against the address of the balancer. The
counts live in the `beffroi.load` cache pool, on `cache.app`, so two containers count together when they share
its directory ([what the processes share](deployment.md#what-the-processes-share)). A number too low on
`/token` or on `/jwks` refuses the deployment's own clients, so a deployment sets them from what its own
clients send.

## `journal`

How long an act of the journal is kept before the timed step forgets it: `BEFFROI_JOURNAL_RETENTION` days, 180
in `.env`. What a client was given of a person in an act is forgotten with that act. Nothing turns the journal
on or off.

## `history`

How long a change a person made to their claims is kept before the timed step forgets it:
`BEFFROI_HISTORY_RETENTION` days, 180 in `.env`, the retention of the journal too, a change and the act that
announced it being two halves of one answer.

## `geoip`

Where the GeoLite2 databases that place the address of a request are kept, and the licence key of the MaxMind
account they are downloaded under. MaxMind publishes them under its own licence, so nothing is shipped, and a
deployment that names no key downloads nothing: every flow is served, and a provenance says an address and no
place.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    geoip:
        storage: '%kernel.project_dir%/var/geoip'
        license_key: '%env(GEOIP_LICENSE_KEY)%'
```

`.env` leaves `GEOIP_LICENSE_KEY` empty. Once a deployment names its key, a weekly timed step downloads the
databases, and `bin/console beffroi:geoip:refresh` does it at once.

## `passwords`

The list of compromised passwords a password is compared with before it is written (NIST SP 800-63B
§3.1.1.2). How long a password has to be and how hard it is to guess are rules of the core, and no option
lowers them.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    passwords:
        breached:
            endpoint: '%env(BEFFROI_BREACHED_PASSWORDS_ENDPOINT)%'
            timeout: '%env(float:BEFFROI_BREACHED_PASSWORDS_TIMEOUT)%'
```

`BEFFROI_BREACHED_PASSWORDS_ENDPOINT` names the list, `https://api.pwnedpasswords.com/range/` for Pwned
Passwords, and `.env` leaves it empty: no list is asked and nothing of a password leaves the deployment.
Named, the endpoint receives the first five hexadecimal characters of the SHA-1 of a password, and the rest is
compared locally. A password the list counts is refused, and so is one the list could not be asked about
within `BEFFROI_BREACHED_PASSWORDS_TIMEOUT`, two seconds in `.env`. A password already set is looked up again
after a login that used it, on the asynchronous lane, once its last answer is thirty days old.

[:beffroi-arrow-right: Passwords](../core/credentials/passwords.md)

## `interaction`

How the `login_hint` of an authorization request is read (OIDC Core §3.1.2.1), which
`BEFFROI_INTERACTION_LOGIN_HINT` names: `sub`, the subject the provider issued to that client, as in `.env`;
`username`, the name a person signs in with; or `none`, which leaves the hint to a class tagged
`beffroi.oidc.login_hint`, and the application tags none, so the image then reads no hint. It is read one way
and never searched, and the login page offers the name of the person it names.

[:beffroi-arrow-right: Interactions](../oidc/interactions.md)

## `back_channel_logout`

How a logout token is posted to a client that registered a `backchannel_logout_uri` (Back-Channel Logout 1.0
§2.5), which five variables time, `BEFFROI_BACK_CHANNEL_LOGOUT_TIMEOUT` and the four of its retries: with the
values of `.env`, five seconds an attempt, then six retries, two seconds after the first failure and three
times longer each time, a minute at most. The retry schedule is the one of every notification the provider
carries to a third party, on the `async_notifications` transport of the application: the logout tokens, the
notifications of the backchannel authentication flow, and the pushes that tell a person something waits for
them.

The schedule is also the `exp` of a logout token, 235 seconds with the values of `.env`, and a retiring
signing key stays published that long at least, so that the provider stops trying when what it sends stops
being verifiable. The transport retries with that very schedule, and `bin/console beffroi:doctor` says whether
the transport a logout token is sent to does.

[:beffroi-arrow-right: Logout](../oidc/logout.md) and [Messenger](messenger.md)

## `backchannel_authentication`

How the `login_hint` of a backchannel authentication request is read (CIBA Core §7.1), which
`BEFFROI_BACKCHANNEL_AUTHENTICATION_LOGIN_HINT` names under the three readings of `interaction`, `sub` in
`.env`, and how long one call to a client in `ping` mode may take, `BEFFROI_CLIENT_NOTIFICATION_TIMEOUT`,
three seconds in `.env`. `none` leaves the hint to a class tagged `beffroi.oidc.ciba_user_hint`, and the one
the application tags reads the `id_token_hint` instead. Nothing here opens the flow: a client takes part in it
by registering its grant and a delivery mode.

[:beffroi-arrow-right: Backchannel authentication](../oidc/grants/backchannel-authentication.md)

## `web_push`

Whether the provider reaches people through the push services of their browsers (RFC 8030). Naming a
`subject` turns it on: a `mailto:` or `https:` URI at which a push service can reach the operator (RFC 8292
§2.1). Its services and routes are always wired, and the file reads the subject from
`BEFFROI_WEB_PUSH_SUBJECT`, which `default::` makes no subject at all when it is empty: web push then serves
nothing, no push leaves the deployment, and the page where a browser would subscribe says so.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    web_push:
        subject: '%env(default::BEFFROI_WEB_PUSH_SUBJECT)%'
        timeout: '%env(float:BEFFROI_WEB_PUSH_TIMEOUT)%'
```

`.env` names the contact of the development stack, `mailto:operator@op.localhost`, so web push is on in the
image: a deployment names its own contact, or empties the variable to turn it off. The push is signed with the
application server key of the tenant, drawn like every other key of the tenant:

``` bash
bin/console beffroi:keys:generate --algorithm=VAPID
```

[:beffroi-arrow-right: Web push](web-push.md)

## `client_authentication`

What a client assertion is held to (RFC 7523 §3), how far ahead its `exp` may be and how much clock it is
allowed, and what one read of a `jwks_uri` may cost: its timeout, its size, how long its keys are kept and how
often an unknown `kid` may read it again. The bounds of a read are those of every published key set the
provider reads, the clients' and the trusted issuers'. The file reads them from
`BEFFROI_CLIENT_ASSERTION_MAX_LIFETIME`, `BEFFROI_CLIENT_ASSERTION_LEEWAY` and the four `BEFFROI_JWKS_URI_*`
variables. Which methods a client may authenticate with is the wiring and its registration, and nothing of
this section.

[:beffroi-arrow-right: Client authentication](../oidc/client-authentication.md)

## `request_objects`

What a request object is held to (RFC 9101 §4), how long it may stand and how much clock it is allowed, and
what one read of a `request_uri` may cost while the browser of a person waits on it, which the file reads from
the four `BEFFROI_REQUEST_OBJECT_*` variables. Which algorithm verifies an object is the registration of the
client.

[:beffroi-arrow-right: Request objects](../oidc/request-objects.md)

## `dpop`

What a proof of possession is held to (RFC 9449): its age, the clock allowed, and whether it carries a nonce of
the provider (RFC 9449 §8). A client that sends no proof is not concerned.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    dpop:
        proof_max_age: '%env(int:BEFFROI_DPOP_PROOF_MAX_AGE)%'
        leeway: '%env(int:BEFFROI_DPOP_LEEWAY)%'
        nonce:
            required: '%env(bool:BEFFROI_DPOP_NONCE_REQUIRED)%'
            ttl: '%env(int:BEFFROI_DPOP_NONCE_TTL)%'
```

`.env` asks for no nonce, `BEFFROI_DPOP_NONCE_REQUIRED=false`, and `true` asks one of every proof.
`nonce.required` is read once, when the port that checks the proofs is built.

[:beffroi-arrow-right: DPoP](../oidc/sender-constrained/dpop.md)

## `trusted_issuers`

The issuers whose assertions the tenant accepts as an authorization grant (RFC 7523 §2.1). Whoever holds the
signing key of one of them can name a user of the tenant and be answered with an access token, so each one is
declared whole: its keys, the algorithms it signs with, the clients that may present its assertions, the
source of the identities it names and the scopes it is trusted for. `.env` declares none, and the grant issues
no token on the image whatever this section names: it addresses a token to a resource the client registered,
and no client of the image registers one ([JWT bearer](../oidc/grants/jwt-bearer.md)).

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    trusted_issuers: '%env(json:BEFFROI_TRUSTED_ISSUERS)%'
```

`BEFFROI_TRUSTED_ISSUERS` carries the section whole, a JSON document keyed by the `iss` of each issuer, whose
members [the reference](../reference/configuration.md#trusted_issuers) lists. The `sub` of an assertion names
a user of the tenant only through a linked identity of the source `identity_provider` names, and no user is
ever created from an assertion.

[:beffroi-arrow-right: The JWT bearer grant](../oidc/grants/jwt-bearer.md)

## `clients`

The clients a file of the application declares, keyed by `client_id`, each read like a registration of RFC
7591 §2. The application's file leaves the section empty, and no variable sets it:

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients: []
```

The image declares no client: a client of a deployment registers itself, at the endpoint `client_registration`
opens ([dynamic registration](../oidc/dynamic-registration.md)). The development configuration,
`config/packages/dev/beffroi.yaml`, which the image leaves out, declares clients here: those of the OpenID
conformance suite and of the demonstrations.

This page describes a declared client only as far as it explains the section, its shape being the one of a
registration. A declared client is read by the reader of a registration and held to the same rules ([what a
registration has to hold](../oidc/clients.md#what-a-registration-has-to-hold)), with three differences. Its
key is its `client_id`, and its secret is written in `secret`, which the development configuration reads from
an environment variable: the provider draws both for a client that registers itself. The secret is hashed when
the client is first read, except for `client_secret_jwt`, which needs the secret itself. And what a declared
client leaves out is the provider's convenience rather than RFC 7591 §2: the browser flow and its renewal, the
scopes `openid profile email`, and the first wired method of authentication, `client_secret_basic`.

A declared client may also carry the members of the deployment, `requires_consent`, `requires_pkce`,
`access_token_format`, `resources`, `token_exchange`, `may_act` and `require_sender_constrained_tokens`, which
a registration is refused for. No client of the image carries one, and [what the image does not
set](../oidc/clients.md#what-the-image-does-not-set) says what every client of the image has instead.

[:beffroi-arrow-right: Clients](../oidc/clients.md) and [your first client](../getting-started/your-first-client.md)

## `self_client`

The application as a client of the provider it serves, so that a firewall of the application signs its users
in there with Symfony's `oidc_login`. Written, it names the routes the application is reached at, the callback
of that firewall in `redirect_route` and, if it wants one, the page to come back to after a logout in
`post_logout_route`, and the provider registers the URLs the router writes for them in the context of the
issuer. Its `client_id` is `app` unless it names another, its `secret` is one environment variable and never
the secret of the kernel, it is never shown the consent page, and it takes the defaults of a declared client
for everything else. The firewall reads the issuer, the identifier and the secret from three container
parameters, `beffroi.self_client.issuer`, `beffroi.self_client.client_id` and `beffroi.self_client.secret`.

The application's file does not write the section, and no variable sets it: the image is no client of its own
provider, and its pages sign a person in with the logins of the provider itself.

## `client_registration`

Whether a client nobody declared may register itself (RFC 7591), and on what authority, which in the image is
how every client comes to exist. `BEFFROI_REGISTRATION_MODE` names the mode, and `.env` leaves it empty: the
tenant has no registration endpoint, none in its discovery document, and `404` on the wire. A mode opens it:
`initial_access_token`, a token the tenant issues, limits and revokes; `software_statement`, a statement
signed by an authority the tenant pins in `BEFFROI_REGISTRATION_STATEMENT_ISSUERS`; or `open`, no credential
at all, for a tenant with no real user.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    client_registration:
        mode: '%env(BEFFROI_REGISTRATION_MODE)%'
        default_scope: '%env(BEFFROI_REGISTRATION_DEFAULT_SCOPE)%'
        keep_a_client_unused_for: '%env(int:BEFFROI_REGISTRATION_KEEP_A_CLIENT_UNUSED_FOR)%'
        keep_a_client_never_used_for: '%env(int:BEFFROI_REGISTRATION_KEEP_A_CLIENT_NEVER_USED_FOR)%'
        sector_identifier_timeout: '%env(float:BEFFROI_REGISTRATION_SECTOR_IDENTIFIER_TIMEOUT)%'
        sector_identifier_max_size: '%env(int:BEFFROI_REGISTRATION_SECTOR_IDENTIFIER_MAX_SIZE)%'
        statement_max_lifetime: '%env(int:BEFFROI_REGISTRATION_STATEMENT_MAX_LIFETIME)%'
        statement_leeway: '%env(int:BEFFROI_REGISTRATION_STATEMENT_LEEWAY)%'
        statement_issuers: '%env(json:BEFFROI_REGISTRATION_STATEMENT_ISSUERS)%'
```

Under `BEFFROI_REGISTRATION_MODE=initial_access_token`, a client registers with a token the console issues:

``` bash
bin/console beffroi:client:token:issue 'Partner integration' --registrations=5 --days=7
```

The name says later which integration a token was for. Without the options, a token registers one client and
is worth thirty days; its value is printed once, and the provider keeps only its digest.

A client that registered itself is deleted after ninety days without use, or after seven days when it was
never used, the values of `.env` for `BEFFROI_REGISTRATION_KEEP_A_CLIENT_UNUSED_FOR` and
`BEFFROI_REGISTRATION_KEEP_A_CLIENT_NEVER_USED_FOR`. The rest of the section bounds the read of a
`sector_identifier_uri` and the software statements, and names the scopes of a client that asks for none,
`BEFFROI_REGISTRATION_DEFAULT_SCOPE`, `openid` alone while it is empty. The file does not write
`exempt_confidential_clients_from_pkce`, which exempts from PKCE the confidential clients of a tenant whose
clients send no `code_challenge`, and never a public one: no variable sets it, and every client of the image
registers with PKCE required, as [what the image does not set](../oidc/clients.md#what-the-image-does-not-set)
says.

[:beffroi-arrow-right: Dynamic registration](../oidc/dynamic-registration.md)

## `saml`

The SAML roles of the tenant, the peers of each, and the SAML keys. Whether a role is on is a variable, read
when the container builds what the role changes: `.env` turns the identity provider on and the service
provider off. A role that is off serves nothing and answers `404` where its metadata would be. The peers of
each role are a JSON document a variable carries whole, `{}` for both in `.env`, and the peers of a role that
is off are refused at their first use.

| Key | What it is | Its variables | The page |
|---|---|---|---|
| `keys` | The rotation of every SAML key, the signing key of both roles and the keys upstream identity providers encrypt for | `BEFFROI_SAML_KEY_STAGING_DELAY` and `BEFFROI_SAML_KEY_AGE` | [The identity provider](../saml/identity-provider.md) |
| `metadata` | The `cacheDuration` of the metadata of both roles | `BEFFROI_SAML_METADATA_CACHE_DURATION` | [The identity provider](../saml/identity-provider.md) |
| `identity_provider` | The tenant as an identity provider | `BEFFROI_SAML_IDENTITY_PROVIDER` and `BEFFROI_SAML_WANT_AUTHN_REQUESTS_SIGNED` | [The identity provider](../saml/identity-provider.md) |
| `service_provider` | The tenant as a service provider to identity providers upstream of it | `BEFFROI_SAML_SERVICE_PROVIDER` and `BEFFROI_SAML_SERVICE_PROVIDER_ENTITY_ID` | [Upstream identity providers](../saml/upstream-identity-providers.md) |
| `service_providers` | The applications that sign their users in through the identity provider | `BEFFROI_SAML_SERVICE_PROVIDERS` | [Service providers](../saml/service-providers.md) |
| `identity_providers` | The identity providers upstream of the service provider, and the e-mail domains each answers for | `BEFFROI_SAML_IDENTITY_PROVIDERS` | [Upstream identity providers](../saml/upstream-identity-providers.md) |

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    saml:
        keys:
            staging_delay: '%env(int:BEFFROI_SAML_KEY_STAGING_DELAY)%'
            age: '%env(int:BEFFROI_SAML_KEY_AGE)%'
        metadata:
            cache_duration: '%env(int:BEFFROI_SAML_METADATA_CACHE_DURATION)%'
        identity_provider:
            enabled: '%env(bool:BEFFROI_SAML_IDENTITY_PROVIDER)%'
            want_authn_requests_signed: '%env(bool:BEFFROI_SAML_WANT_AUTHN_REQUESTS_SIGNED)%'
        service_provider:
            enabled: '%env(bool:BEFFROI_SAML_SERVICE_PROVIDER)%'
            entity_id: '%env(default::BEFFROI_SAML_SERVICE_PROVIDER_ENTITY_ID)%'
        service_providers: '%env(json:BEFFROI_SAML_SERVICE_PROVIDERS)%'
        identity_providers: '%env(json:BEFFROI_SAML_IDENTITY_PROVIDERS)%'
```

`keys` and `metadata` belong to no role and turn neither on. With the values of `.env`, a new SAML key is
published seven days before it is used and works a year, and the metadata of both roles tell a peer to read
them again every day: the `cacheDuration` is shorter than the staging delay of the SAML keys, or the provider
refuses it.
