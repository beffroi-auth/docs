---
title: Configuration reference
description: Every option of the tree under `beffroi`, with its type, its default and what it decides.
---

# Configuration reference

Every option the bundle reads under `beffroi`, section by section, in the order the bundle builds the tree.
[Configuration](../symfony-bundle/configuration.md) says what each section is for and when a deployment
needs it; this page is the list.

!!! note "Your installation is the authority"

    This page is written by hand from the configuration classes of the bundle, and nothing generates it. The
    tree your version validates is the one your own installation prints, with its defaults:

    ``` bash
    bin/console config:dump-reference beffroi
    bin/console config:dump-reference beffroi tokens
    ```

    The second form prints one section. Where this page and the command disagree, the command describes
    the version you run.

## Reading the tables

- **A path** is written from the section it belongs to: `look.logo_uri` under `tenant` is
  `beffroi.tenant.look.logo_uri`.
- **A duration** is in seconds, except the two retentions, which are in days.
- **A bound** is in the type column. A value written in the file outside it is refused when the container is
  built, as is an unknown key at any level of the tree.
- **required** means the configuration is refused without it. **none** means the option is absent until it
  is written, and the last column says what its absence decides.
- **A keyed section**, `clients` for instance, holds one entry per key, and the key is a value, the
  `client_id` there. It is kept exactly as written, never normalised.
- **A wired name** is checked against what the provider is wired with: an algorithm, a grant, a method of
  client authentication. The table names what the bundle wires; a deployment that changes the wiring changes
  the list, and a refusal names the names that are wired.

## `tenant`

The one tenant of the deployment: required. [Tenants](../core/tenants.md) is what a tenant is. A value the
tenant cannot hold is refused when the provider builds the tenant, which it does before serving anything of
it.

| Option | Type | Default | What it decides |
|---|---|---|---|
| `issuer` | string | required | The issuer identifier (OIDC Discovery 1.0 §3), and the URL every endpoint is served under: an absolute `https` URL with no query, no fragment, no credentials and no trailing slash. Plain `http` is accepted on a loopback host only: `localhost`, a name under it, `127.0.0.0/8` or `[::1]` |
| `slug` | string, not empty | `default` | The stable name of the tenant, from which its identifier is derived. Renaming it is creating another tenant |
| `name` | string | the host of the issuer | What the pages call the tenant |
| `look.logo_uri` | string | none | The logo every page shows: an absolute `https` URL with no fragment and no credentials, plain `http` on a loopback host only. The browser of the visitor loads it, never the provider. The consent page adds its origin to the `img-src` of the `Content-Security-Policy` the application sends; every other page shows it under that policy as the application writes it, so a logo served from another origin is named in its `img-src` |
| `look.primary_color` | string | none | The colour the buttons and the links of the pages are drawn in: `#` and three or six hexadecimal digits, as `#1b4b8f`. Declared with `primary_content_color` or not at all |
| `look.primary_content_color` | string | none | The colour of what is written on `primary_color`, in the same notation |
| `self_served_claims` | list of strings | none | The claims of OIDC Core §5.1 the people of the tenant may change of themselves on the page of their account, among the claims the provider is wired with: `name`, `given_name`, `family_name`, `middle_name`, `nickname`, `preferred_username`, `birthdate`, `gender`, `locale`, `zoneinfo`, `profile`, `picture`, `website` and `phone_number` in the bundle |
| `authentication_classes` | map of class name to predicate name | the default policy | The `acr` vocabulary of the tenant, in the order a session is answered in, each class on a predicate the provider is wired with: `phishing_resistant_hardware`, `phishing_resistant`, `two_factors` and `single_factor` in the bundle. Left empty, the default policy answers: `phrh`, `phr`, `2` and `1`, on those four in that order. A policy names one class at least on a predicate every login satisfies, `single_factor` among the four, so that every session has an `acr`. It never names `0` (OIDC Core §2), and the names of OpenID Connect EAP ACR Values 1.0 keep their meaning: `phrh` stands on `phishing_resistant_hardware` only, `phr` on it or on `phishing_resistant` |

## `keys`

Where the keys of the tenant are sealed, stored and rotated: required. The figures of rotation apply to every
key of the tenant but its SAML keys, which take theirs from
[`saml.identity_provider`](#samlidentity_provider).

| Option | Type | Default | What it decides |
|---|---|---|---|
| `kms` | string, not empty | required | The name of the key management client the private keys are sealed with, an entry of `key_management.clients`. A name nothing is registered under fails the build of the container, naming the clients that are registered. The client seals and opens keys, and never signs |
| `key_id` | string, not empty | required | The key of that client the keys of the tenant are sealed under, in the terms of its backend: the identifier of a sodium key, a Vault transit key name, an ARN. `{tenant}` in it stands for the slug of the tenant, one master key per tenant. The data keys that seal personal data are wrapped under the same key |
| `data_key_secrets` | list of strings, not empty, one at least | `['%kernel.secret%']`, the secret of the kernel | The secrets every data key of personal data is bound to its reference and its scope under, which the database does not hold. The first binds a new key, a key bound under any of them opens, and one bound under a secret no longer listed opens nothing, nor does what it sealed. A single string is read as a list of one. A secret is replaced by writing the new one first, then running `beffroi:data-keys:rewrap` towards the client that already wraps the keys, then dropping the old one: [personal data](../core/personal-data.md#rotating-the-secret-that-binds-them) |
| `storage` | string, not empty | `%kernel.project_dir%/var/keys` | The directory of the sealed keys, one file per key and per tenant, and of the pairwise salt of each tenant beside them (OIDC Core §8.1) |
| `jwks_max_age` | integer, 0 or more | `300`, five minutes | How long a relying party may keep the JWK Set (RFC 7517 §5): its `Cache-Control: public, max-age`, which the SAML metadata are served with as well. The default staging delay derives from it |
| `staging_delay` | integer, 0 or more | `jwks_max_age` plus 60, six minutes with the default | How long a new key is published before it signs. The default covers a relying party holding a copy of the JWK Set as old as `jwks_max_age`, and the sixty seconds after which Symfony's `oidc_login` reads the set again for a `kid` it does not hold |
| `age` | integer, 1 or more | `7776000`, ninety days | How long a key works before the timed step stages a successor behind it, counted from its activation. It is longer than the time a retiring key stays published, the longest lifetime of what is bound to a key of that use, or the rotation refuses it |

## `webauthn`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `metadata_storage` | string, not empty | `%kernel.project_dir%/var/webauthn` | The directory of the FIDO metadata an attestation is checked against: the documents `beffroi:webauthn:mds-refresh` verified and `beffroi:webauthn:mds-import` stored. It is empty until one of them runs, which enrolling a passkey does not need |

## `mutual_tls`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `origin` | string | none | The scheme and the authority, without a path, of the host whose TLS listener asks for a client certificate, as `https://mtls.op.example.com`. The endpoints are announced under it in `mtls_endpoint_aliases` (RFC 8705 §5). Absent or empty, no alias is announced, and a client authenticating by certificate reaches the ordinary endpoints |

## `tokens`

Lifetimes and intervals, in seconds.

| Option | Type | Default | What it decides |
|---|---|---|---|
| `authorization_code_ttl` | integer, 1 to 600 | `60`, one minute | How long an authorization code can be spent. RFC 6749 §4.1.2 recommends ten minutes at most, which is the bound |
| `access_token_ttl` | integer, 1 or more | `600`, ten minutes | How long an access token is valid, in either shape: a JWT cannot be revoked, and an opaque token gets the same lifetime |
| `id_token_ttl` | integer, 1 or more | `600`, ten minutes | How long an ID token is valid |
| `request_uri_ttl` | integer, 1 to 600 | `60`, one minute | How long a `request_uri` answered by the pushed authorization request endpoint lives (RFC 9126 §2.2) |
| `device_code_ttl` | integer, 1 to 1800 | `600`, ten minutes | How long a device code and its user code live (RFC 8628 §3.2) |
| `device_code_interval` | integer, 1 to 30 | `5` | How long a device waits between two polls of the token endpoint (RFC 8628 §3.2). One that polls sooner is answered `slow_down`, and its interval grows by five seconds (RFC 8628 §3.5) |
| `backchannel_authentication_ttl` | integer, 1 to 3600 | `300`, five minutes | How long a backchannel authentication request lives when the client sends no `requested_expiry` (CIBA Core §7.3), never longer than `backchannel_authentication_max_requested_expiry` |
| `backchannel_authentication_max_requested_expiry` | integer, 1 to 3600 | `1800`, thirty minutes | The longest lifetime a client may ask for with `requested_expiry` (CIBA Core §7.1). A request that asks for more is served this, not refused |
| `backchannel_authentication_interval` | integer, 1 to 30 | `5` | How long a client waits between two polls of the token endpoint for a backchannel request (CIBA Core §7.3). One that polls sooner is answered `slow_down`, and its interval grows by five seconds (CIBA Core §11) |
| `refresh_token_ttl` | integer, 1 or more | `2592000`, thirty days | The sliding lifetime of a refresh token, renewed at each rotation. The tree refuses one longer than `refresh_token_absolute_ttl` |
| `refresh_token_absolute_ttl` | integer, 1 or more | `7776000`, ninety days | The lifetime of a family of refresh tokens, counted from the authorization that started it. No rotation extends it |

## `load`

The two budgets every request is counted against. A request over a budget is answered `429` with a
`Retry-After` header (RFC 6585 §4). Both count over a sliding window, in the `beffroi.load` cache pool.

| Option | Type | Default | What it decides |
|---|---|---|---|
| `origin.limit` | integer, 1 or more | `2400` | Requests taken from one client address in the window, on every route of the bundle and for every tenant of the deployment, counted before anything is verified |
| `origin.interval` | integer, 1 or more | `60`, one minute | The window of that budget |
| `client.limit` | integer, 1 or more | `1200` | Requests taken from one client of one tenant in the window, counted once the client has authenticated |
| `client.interval` | integer, 1 or more | `60`, one minute | The window of that budget |

## `journal`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `retention` | integer, 1 or more | `180` | Days an act of the journal is kept before the timed step forgets it, and with it what a client was given of a person in that act |

## `history`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `retention` | integer, 1 or more | `180` | Days a change a person made to their claims is kept before the timed step forgets it |

## `geoip`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `storage` | string, not empty | `%kernel.project_dir%/var/geoip` | The directory of the GeoLite2 databases that place the address of a request: the files `beffroi:geoip:refresh` and the weekly timed step store. Every flow is served while it is empty |
| `license_key` | string | empty | The licence key of the MaxMind account the databases are downloaded under. Empty, nothing is downloaded, and a provenance says an address and no place |

## `passwords`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `breached.endpoint` | string | empty | The base URL of a range endpoint in the shape of Pwned Passwords, as `https://api.pwnedpasswords.com/range/`: the first five hexadecimal characters of the SHA-1 of a password are appended to it, the rest is compared locally, and no API key is needed. Empty, nobody is asked. Named, a password the list counts is refused, and one the list could not be asked about is not written either |
| `breached.timeout` | number, 0.1 or more | `2.0` | Seconds the whole exchange with the list may take where somebody waits for it: the command that sets a password, and the page where a person replaces their own |

## `interaction`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `login_hint` | `sub`, `username` or `none` | `sub` | What the `login_hint` of an authorization request names, read one way and never searched (OIDC Core §3.1.2.1): `sub`, the subject the provider issued to that client; `username`, the name the person signs in with; `none`, nothing of the bundle, for a deployment that tags a reading of its own `beffroi.oidc.login_hint`. The login page offers the name of the person the hint names, and nothing when it names nobody |

## `back_channel_logout`

How a logout token reaches a client that registered a `backchannel_logout_uri`. The four `retry_*` options
are the schedule of every notification the provider carries to a third party, on the `async_notifications`
transport the bundle configures: logout tokens, the notifications of the backchannel authentication flow, and
the pushes that tell a person something waits for them.

| Option | Type | Default | What it decides |
|---|---|---|---|
| `timeout` | number, 0.1 or more | `5.0` | Seconds one attempt to post a logout token is given, connection included (Back-Channel Logout 1.0 §2.5) |
| `retries` | integer, 0 or more | `6` | How many times a notification that did not reach its client is sent again |
| `retry_delay` | integer, 1 or more | `2` | Seconds before the first retry |
| `retry_multiplier` | integer, 1 or more | `3` | What each wait is multiplied by to give the next one |
| `retry_max_delay` | integer, 1 or more | `60` | Seconds no wait exceeds |

With the defaults the waits are 2, 6, 18, 54, 60 and 60 seconds. The `exp` of a logout token is the whole
schedule, its waits and one `timeout` per attempt, 235 seconds with the defaults, and a signing key another
key takes over from stays in the JWK Set that long at least, so that a logout token still on its way
verifies.

## `backchannel_authentication`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `login_hint` | `sub`, `username` or `none` | `sub` | What the `login_hint` of a backchannel authentication request names (CIBA Core §7.1), under the three readings of `interaction.login_hint`; `none` is for a deployment that tags its own `beffroi.oidc.ciba_user_hint`. CIBA Core §15 asks for an identifier that says nothing outside the provider, which a `sub` is and a username is not |
| `client_notification_timeout` | number, 0.1 or more | `3.0` | Seconds one call to the notification endpoint of a client in `ping` mode is given, connection included (CIBA Core §10.2). It is retried on the schedule of `back_channel_logout` |

## `web_push`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `subject` | string, not empty | none | The `sub` of the token the provider signs for a push service (RFC 8292 §2.1): a `mailto:` or `https:` URI at which the operator of the deployment can be reached. Naming one turns web push on, with the application server key of the tenant, a P-256 key the key commands call `VAPID`. Absent, no push leaves the deployment, and the page where a browser would subscribe says so |
| `timeout` | number, 0.1 or more | `3.0` | Seconds one push to one push service is given, connection included. It is retried on the schedule of `back_channel_logout` |

## `client_authentication`

What a client assertion and a published key set are held to. The four `jwks_*` options bound every key set
the provider reads behind a `jwks_uri`: the clients' and the [trusted issuers'](#trusted_issuers).

| Option | Type | Default | What it decides |
|---|---|---|---|
| `assertion_max_lifetime` | integer, 1 or more | `300`, five minutes | How far ahead of the request the `exp` of a client assertion may be (RFC 7523 §3). The assertions of a trusted issuer are held to the same |
| `assertion_leeway` | integer, 0 or more | `30` | Seconds allowed for the clock of a client or of a trusted issuer, both ways |
| `jwks_timeout` | number, 0.1 or more | `3.0` | Seconds one read of a `jwks_uri` is given, connection included |
| `jwks_max_size` | integer, 1 or more | `65536` | Bytes a `jwks_uri` may answer before the read stops |
| `jwks_ttl` | integer, 1 or more | `86400`, one day | How long the keys read from a `jwks_uri` are kept, in the `beffroi.client_keys` and `beffroi.issuer_keys` cache pools |
| `jwks_refetch_cooldown` | integer, 0 or more | `300`, five minutes | Seconds between two reads of the same `jwks_uri` when a signature names a `kid` the kept set does not hold |

## `request_objects`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `max_lifetime` | integer, 1 or more | `3600`, one hour | How long a request object may stand: its `exp` is at most this long after its `nbf` (RFC 9101 §4) |
| `leeway` | integer, 0 or more | `30` | Seconds allowed for the clock of a client, both ways |
| `timeout` | number, 0.1 or more | `3.0` | Seconds one read of a `request_uri` is given, connection included, while the browser of a person waits. Only a URL the client registered is read, and no redirect is followed |
| `max_size` | integer, 1 or more | `65536` | Bytes a `request_uri` may answer before the read stops |

## `dpop`

| Option | Type | Default | What it decides |
|---|---|---|---|
| `proof_max_age` | integer, 1 or more | `60`, one minute | How long a proof stands, from its `iat` (RFC 9449 §4.3) |
| `leeway` | integer, 0 or more | `30` | Seconds allowed for the clock of a client, both ways |
| `nonce.required` | boolean | `false` | Whether a proof carries a nonce of the provider (RFC 9449 §8). On, a proof without a valid one is refused with `use_dpop_nonce` and a fresh nonce in the `DPoP-Nonce` header. It decides which class the container wires, so it is written as `true` or `false` in the file |
| `nonce.ttl` | integer, 1 or more | `300`, five minutes | How long a nonce the provider issued is accepted |

## `trusted_issuers`

The issuers whose assertions the tenant accepts as an authorization grant (RFC 7523 §2.1), one entry per
issuer; none by default, and the grant then serves nobody. A declaration that does not hold together is
refused when the provider first reads the trusted issuers.

| Option | Type | Default | What it decides |
|---|---|---|---|
| The key | string | | The `iss` of its assertions, compared byte for byte: an absolute URI without a fragment (RFC 7519 §4.1.1) |
| `jwks` | JWK Set | none | The public keys of the issuer, inline (RFC 7517 §5), and the only keys an assertion of it is verified against, whatever its header names (RFC 8725 §3.10). One of `jwks` and `jwks_uri`, never both |
| `jwks_uri` | string | none | Where the issuer publishes its JWK Set instead: `https`, or plain `http` on a loopback host. It is read with one `GET`, no redirect followed, kept, and read again at most once per `client_authentication.jwks_refetch_cooldown` for a `kid` the kept set does not hold |
| `signing_algorithms` | list of strings | required | The JWS algorithms its assertions may be signed with, one at least, among those the provider verifies: `RS256`, `PS256`, `ES256` and `EdDSA` in the bundle |
| `clients` | list of strings | required | The clients that may present its assertions at the token endpoint, by `client_id`, one at least |
| `identity_provider` | string | required | The source of the linked identities its subjects name: the `sub` of an assertion is a user of the tenant only when a linked identity of that source says so, and no user is ever created from one |
| `trusted_scopes` | list of strings | required | What the issuer is trusted for, one scope at least. The scopes of a response are within these, within what the client registered and within what the request asked for; `openid` buys nothing here, the grant refusing it |

## `clients`

The clients the deployment declares, one entry per client; none by default. Each one is read like a
registration of RFC 7591 §2 and OIDC Registration §2, and a declaration that does not hold together is
refused when the provider first reads its clients, naming the client, the option and the rule.
[Clients](../oidc/clients.md) is what a client is.

| Option | Type | Default | What it decides |
|---|---|---|---|
| The key | string | | The `client_id`, kept exactly as written: printable ASCII with no leading or trailing space (RFC 6749 appendix A.1) |
| `client_name` | string | the `client_id` | The name a person reads on the consent page (OIDC Registration §2) |
| `client_uri` | string | none | The home page of the client, linked from the consent page. Like every URL a client registers: absolute, `https` or plain `http` on a loopback host, no fragment, no credentials and no scheme of its own |
| `logo_uri` | string | none | The logo the consent page shows for the client, loaded by the browser of the person and never by the provider |
| `policy_uri` | string | none | How the client uses the data it is given, linked from the consent page |
| `tos_uri` | string | none | The terms of service of the client, linked from the consent page |
| `contacts` | list of strings | none | Ways to reach the people responsible for the client, typically e-mail addresses. No page shows them |
| `secret` | string | none | The secret of a client authenticating with `client_secret_basic`, `client_secret_post` or `client_secret_jwt`, which need one, and that every other method refuses: 32 visible ASCII characters at least, generated rather than chosen. It is hashed when the client is first read, except for `client_secret_jwt`, which verifies a MAC with the secret itself |
| `redirect_uris` | list of strings | none | Where the browser may be sent back, each compared byte for byte with the `redirect_uri` of a request (RFC 6749 §3.1.2.3). A public client writes plain `http` on `127.0.0.1` or `[::1]` only, never on a name, and such a URI matches on whatever port the request names (RFC 8252 §7.3). A client registered for `authorization_code` registers one at least, and a client registered for no such grant registers none |
| `post_logout_redirect_uris` | list of strings | none | Where the browser may be sent after a logout, compared byte for byte with the `post_logout_redirect_uri` of the request (OIDC RP-Initiated Logout 1.0 §3), under the rules of `redirect_uris` |
| `grant_types` | list of strings | `authorization_code` and `refresh_token` | What the client may ask for at the token endpoint (RFC 7591 §2), among the wired grants: `authorization_code`, `refresh_token`, `client_credentials`, `urn:ietf:params:oauth:grant-type:device_code`, `urn:openid:params:grant-type:ciba`, `urn:ietf:params:oauth:grant-type:token-exchange` and `urn:ietf:params:oauth:grant-type:jwt-bearer` in the bundle. `refresh_token` goes with a grant that issues one, and `client_credentials` with a method that authenticates the client |
| `response_types` | list of strings | none | What the client asks the authorization endpoint to answer with (OIDC Registration §2): `code`, and nothing else. Left out, it is the one its grants answer with; `code` without `authorization_code` is refused |
| `scope` | string | `openid profile email` | The closed list of scopes the client may ask for, space-delimited (RFC 7591 §2, RFC 6749 §3.3). A scope it did not register is refused with `invalid_scope` |
| `token_endpoint_auth_method` | string | the first wired method, `client_secret_basic` | How the client authenticates (OIDC Core §9), among the wired methods: `client_secret_basic`, `client_secret_post`, `private_key_jwt`, `client_secret_jwt`, `tls_client_auth`, `self_signed_tls_client_auth` and `none` in the bundle. `none` makes a public client |
| `requires_consent` | boolean | `true` | Whether the person is asked to consent. `false` is for a first-party application, which is never shown the consent page, `prompt=consent` included |
| `requires_pkce` | boolean | `true` | Whether an authorization request of the client carries a PKCE challenge, `S256` being the only method. `false` is for a confidential client that cannot send one, and is refused for a public client; a challenge the client sends is verified all the same |
| `require_pushed_authorization_requests` | boolean | `false` | The client starts an authorization request only by pushing it (RFC 9126 §6), and any other request of it is refused on a page before its redirect URI is read. The discovery document announces the requirement when every client of the tenant carries it |
| `require_sender_constrained_tokens` | boolean | `false` | A token request of the client proves a certificate (RFC 8705 §3) or a key (RFC 9449 §5), or it is refused rather than answered with bearer tokens (FAPI 2.0 Security Profile §5.3.1) |
| `tls_client_certificate_bound_access_tokens` | boolean | `false` | The tokens of the client are bound to the certificate it presents at the TLS handshake, whichever way it authenticated (RFC 8705 §3.4), and a token request that proves no certificate is refused. A client authenticating by certificate gets bound tokens either way |
| `require_signed_request_object` | boolean | `false` | A request of the client is read only from a request object it signed (RFC 9101 §10.5), wherever the object arrives: in the query, behind a `request_uri`, in a pushed request or in a backchannel authentication request. An unsigned authorization request is refused on a page before its redirect URI is read, an unsigned backchannel one with `invalid_request`. A declaration that names it beside `request_object_signing_alg: none` is refused |
| `id_token_signed_response_alg` | string | the default algorithm, `RS256` | The JWS algorithm the ID tokens and the logout tokens of the client are signed with (OIDC Registration §2), among the wired ones: `RS256`, `PS256`, `ES256` and `EdDSA` in the bundle, the first being the default |
| `id_token_encrypted_response_alg` | string | none | The JWE key management algorithm the signed ID token is encrypted to a key of the client with (OIDC Core §3.1.3.7), among the wired ones: `ECDH-ES+A256KW` and `RSA-OAEP-256` in the bundle. Named with `id_token_encrypted_response_enc` or not at all. Left out, the ID token is signed and not encrypted |
| `id_token_encrypted_response_enc` | string | none | The JWE content encryption algorithm of that ID token, among the wired ones: `A256GCM` in the bundle. OIDC Registration §2 defaults it to an algorithm the bundle does not wire, so it is written whenever `id_token_encrypted_response_alg` is |
| `userinfo_signed_response_alg` | string | none | The JWS algorithm the UserInfo answer of the client is signed with (OIDC Core §5.3.2), among the wired ones. Named, the answer is a JWT served as `application/jwt`, with an `iss` and an `aud` beside the claims; left out, it is plain JSON |
| `userinfo_encrypted_response_alg` | string | none | The JWE key management algorithm the UserInfo answer is encrypted to a key of the client with, named with `userinfo_encrypted_response_enc` or not at all. Without `userinfo_signed_response_alg`, what is encrypted is the plain JSON (OIDC Core §5.3.2) |
| `userinfo_encrypted_response_enc` | string | none | The JWE content encryption algorithm of that answer |
| `authorization_signed_response_alg` | string | the default algorithm, `RS256` | The JWS algorithm of the signed authorization responses of the client (JARM §3): the answers it asks for with the `response_mode` `jwt`, `query.jwt` or `form_post.jwt`, a refusal as well as a code |
| `authorization_encrypted_response_alg` | string | none | The JWE key management algorithm the signed authorization response is encrypted to a key of the client with (JARM §3), named with `authorization_encrypted_response_enc` or not at all |
| `authorization_encrypted_response_enc` | string | none | The JWE content encryption algorithm of that response |
| `access_token_format` | string | the first wired shape, `jwt` | The shape of the access tokens of the client: `jwt`, verified offline against the JWK Set (RFC 9068), or `opaque`, a reference the resource server introspects (RFC 7662) and that can be revoked at once |
| `backchannel_logout_uri` | string | none | Where the provider posts a logout token when a session the client signed in ends (Back-Channel Logout 1.0 §2.2). Absent, the client is not told |
| `backchannel_logout_session_required` | boolean | `false` | The client reads the `sid` of the logout token to know which session ended, and registers a `backchannel_logout_uri`. The provider sends the `sid` either way |
| `frontchannel_logout_uri` | string | none | Loaded in a frame of the logout page when a session the client signed in ends (Front-Channel Logout 1.0 §3). It reaches the client only if the browser sends that client its cookies |
| `frontchannel_logout_session_required` | boolean | `false` | The provider adds `iss` and `sid` to the logout URI of the client (Front-Channel Logout 1.0 §2), which then registers a `frontchannel_logout_uri` |
| `jwks` | JWK Set | none | The public keys of the client, inline (RFC 7591 §2). One of `jwks` and `jwks_uri`, never both, is required of a client that authenticates with `private_key_jwt` or `self_signed_tls_client_auth`, names a `request_object_signing_alg` other than `none`, or asks for an encrypted response |
| `jwks_uri` | string | none | Where the client publishes its JWK Set instead (RFC 7591 §2), read with no redirect followed, under the bounds of `client_authentication` |
| `subject_type` | string | the first wired kind, `public` | The kind of `sub` the client sees for a person (OIDC Core §8): `public` or `pairwise` in the bundle. A `pairwise` client has a sector: its `sector_identifier_uri`, redirect URIs on one host, or, with no redirect URI, its `jwks_uri` |
| `sector_identifier_uri` | string | none | A URL whose host is the sector of the client's pairwise subjects (OIDC Core §8.1). The document behind it is read when a client registers itself (OIDC Registration §5), and never for a declared client |
| `initiate_login_uri` | string | none | Where a third party sends a person to have the client begin a login (OIDC Core §4): `https` on every host, a loopback host included (OIDC Registration §2) |
| `request_object_signing_alg` | string | any wired algorithm | The JWS algorithm the request objects of the client are signed with (OIDC Registration §2), among the wired ones. Left out, any of them verifies an object, and an unsigned object is refused. `none` is the one exception: the objects of the client carry no signature and are read all the same, and a client with `require_signed_request_object` cannot name it |
| `backchannel_token_delivery_mode` | string | none | How the client learns that a backchannel authentication request was answered (CIBA Core §4): `poll` or `ping` in the bundle. There is no default: a client that names none is not a client of that flow, and the backchannel authentication endpoint refuses it |
| `backchannel_client_notification_endpoint` | string | none | Where the provider posts to a `ping` client once its request is answered (CIBA Core §7.1, §10.2). Required with `ping`, and refused with any other mode or with none |
| `resources` | list of strings | none | The resources the client may ask an access token for (RFC 8707 §2), each an absolute URI without a fragment; any other is refused with `invalid_target`. A client that registers none asks for none, and its tokens are addressed to itself |
| `authorization_details_types` | list of strings | none | The types of authorization detail the client may ask for (RFC 9396 §2), among the wired ones; any other is refused with `invalid_authorization_details`. The bundle wires none: a deployment that serves a type tags its class `beffroi.oidc.authorization_detail_type` |
| `token_exchange.subject_token_types` | list of strings | required in the block | The token types the client may present as a `subject_token` or an `actor_token` (RFC 8693 §3), one at least, among the wired ones: `urn:ietf:params:oauth:token-type:access_token` in the bundle |
| `token_exchange.may_act_for_a_user` | boolean | `false` | Whether the client may present a token somebody signed in for. `false` for a service that only exchanges tokens of its own |
| `may_act` | string | none | Who may act for the subject of a token issued to the client (RFC 8693 §4.4), named as a subject. It is written on every token the client receives, and an exchange asked for by anybody else is refused |
| `request_uris` | list of strings | none | The URLs a request object of the client is read from (OIDC Registration §2), compared byte for byte with the `request_uri` of a request, fragment included (OIDC Core §6.2). Any other is refused before anything is fetched |
| `tls_client_auth_subject_dn` | string | none | The subject distinguished name of the certificate of a `tls_client_auth` client (RFC 8705 §2.1.2), in the string form of RFC 4514, as `openssl x509 -noout -subject -nameopt RFC2253` prints it |
| `tls_client_auth_san_dns` | string | none | The `dNSName` of its certificate, compared without regard to case (RFC 4343 §1) |
| `tls_client_auth_san_uri` | string | none | The `uniformResourceIdentifier` of its certificate, compared as written |
| `tls_client_auth_san_ip` | string | none | The `iPAddress` of its certificate, in dotted decimal or colon-delimited hexadecimal, compared as the octets it stands for |
| `tls_client_auth_san_email` | string | none | The `rfc822Name` of its certificate, compared as written (RFC 5321 §2.4) |

The `token_exchange` block is declared by a client registered for the token exchange grant, and refused for
any other. A `tls_client_auth` client names exactly one of the five `tls_client_auth_*` options, and a client
authenticating otherwise names none of them.

## `client_registration`

How a client nobody declared comes to exist (RFC 7591). Without a `mode`, the tenant registers nobody.

| Option | Type | Default | What it decides |
|---|---|---|---|
| `mode` | string | none | What authorises a registration, among the wired modes: `initial_access_token`, a token the tenant issues, limits and revokes (RFC 7591 §1.2); `open`, no credential at all (RFC 7591 §1.3), for a tenant with no real user; `software_statement`, a statement signed by an authority of `statement_issuers` (RFC 7591 §2.3). Absent or empty, the tenant has no registration endpoint: none in its discovery document, and `404` on the wire. A name no wired mode answers to is refused when a registration arrives, naming the wired ones |
| `keep_a_client_unused_for` | integer, 1 or more | `7776000`, ninety days | Seconds a registered client that was used may go unused before it is deleted |
| `keep_a_client_never_used_for` | integer, 1 or more | `604800`, seven days | Seconds a registered client that was never used lives |
| `sector_identifier_timeout` | number, 0.1 or more | `3.0` | Seconds one read of a `sector_identifier_uri` is given, connection included (OIDC Registration §5), when a client registers or replaces itself |
| `sector_identifier_max_size` | integer, 1 or more | `65536` | Bytes such a document may answer before the read stops |
| `statement_issuers` | map | none | The authorities whose software statements the tenant accepts, keyed by the `iss` they sign with, compared byte for byte. With none, the `software_statement` mode registers nobody |
| `statement_issuers.<iss>.jwks` | JWK Set | required | The public keys of the authority, inline (RFC 7517 §5), and the only keys a statement is verified against, whatever its header names (RFC 8725 §3.10) |
| `statement_issuers.<iss>.signing_algorithms` | list of strings | required | The JWS algorithms its statements may be signed with, one at least, among those the provider verifies |
| `statement_max_lifetime` | integer, 1 or more | `300`, five minutes | How far ahead of the request the `exp` of a software statement may be (RFC 7591 §2.3). A statement without an `exp` is refused |
| `statement_leeway` | integer, 0 or more | `30` | Seconds allowed for the clock of an authority, both ways |
| `default_scope` | string | none | What a client that registers itself and names no `scope` is registered with, space-delimited (RFC 7591 §2, RFC 6749 §3.3). Left out, such a client is registered with `openid` alone. A client that names its own scopes keeps them, and a scope written here that the tenant does not offer refuses every registration that names none |
| `exempt_confidential_clients_from_pkce` | boolean | `false` | Whether the confidential clients the tenant registers are registered without the PKCE requirement, for a tenant whose clients send no `code_challenge`. A public client is never exempted, `plain` does not exist, and a challenge a client sends is verified all the same |

## `saml`

The SAML roles of the tenant and its peers. A role that is off wires nothing. Service providers are declared
only while the identity provider is on, and upstream identity providers only while the service provider is
on: the configuration is refused otherwise. A declaration of a peer that does not hold together fails the
build of the container, and one that holds an environment variable fails at its first use.

### `saml.identity_provider`

[The identity provider](../saml/identity-provider.md) is the role.

| Option | Type | Default | What it decides |
|---|---|---|---|
| `enabled` | boolean | `false` | Whether the tenant is a SAML identity provider. Writing the block turns it on unless it says `enabled: false`, and `identity_provider: true` is the short form. Off, the tenant serves no metadata and declares no service provider |
| `want_authn_requests_signed` | boolean | `true` | What the metadata say in `WantAuthnRequestsSigned` (SAML Metadata §2.4.3). It announces, and decides nothing: whether a request needs a signature is decided per service provider |
| `staging_delay` | integer, 0 or more | `604800`, seven days | How long a new SAML key is published before it is used |
| `age` | integer, 1 or more | `31536000`, 365 days | How long a SAML key works before the timed step stages a successor behind it, counted from its activation |
| `cache_duration` | integer, 1 or more | `86400`, one day | The `cacheDuration` of the metadata of both roles (SAML Metadata §2.3.2). It is strictly shorter than `staging_delay`, or the configuration is refused |

`staging_delay` and `age` rotate every SAML key of the tenant, the signing key of both roles and the keys
upstream identity providers encrypt for, whichever role is on, and `cache_duration` is written in the metadata
of both roles.

### `saml.service_provider`

[Upstream identity providers](../saml/upstream-identity-providers.md) is the role.

| Option | Type | Default | What it decides |
|---|---|---|---|
| `enabled` | boolean | `false` | Whether the tenant is a SAML service provider to identity providers upstream of it, with the same short form. Off, nothing of it is wired |
| `entity_id` | string, not empty | the URL of its metadata | The entity ID of the service provider: an absolute URI of 1024 characters at most, with no whitespace, control, format or invisible character, and never the entity ID of the identity provider of the tenant |

### `saml.service_providers`

The service providers of the tenant, one entry per entity ID. [Service providers](../saml/service-providers.md)
is how one is declared.

| Option | Type | Default | What it decides |
|---|---|---|---|
| The key | string | | The entity ID of the service provider, compared exactly with the one of its metadata: 1024 characters at most, no whitespace |
| `metadata` | string, not empty | required | Where its metadata are read from: an `https` URL, no redirect followed, or the absolute path of a file of the deployment |
| `metadata_signers` | list of strings | none | The certificates its metadata are signed by, each the base64 of its DER, sixteen at most. Named, the metadata are verified under them and carry a `validUntil`; left empty, they are trusted by the channel they come through |
| `attributes` | map | none | The claims sent to the service provider, keyed by the name of the attribute each one is sent as, 256 at most. A claim may be sent under several names |
| `attributes.<name>.claim` | string, not empty | required | The claim sent under that name (OIDC Core §5.1), one the provider serves |
| `attributes.<name>.name_format` | `uri`, `basic` or `unspecified` | `uri` | The name format of the attribute (SAML Core §8.2) |
| `attributes.<name>.friendly_name` | string | none | A name a person reads (SAML Core §2.7.3.1), which nothing compares |
| `encrypt_assertions` | boolean | `false` | Its assertions are encrypted for a key of its metadata, which then hold one for encryption or are refused |
| `signs_authn_requests` | boolean | `true` | It signs its authentication requests, and its metadata hold a key for signing or are refused. `false` for one that cannot: its unsigned requests are then accepted, unless its metadata say it signs |

### `saml.identity_providers`

The upstream identity providers of the tenant, one entry per entity ID.
[Upstream identity providers](../saml/upstream-identity-providers.md) is how one is declared.

| Option | Type | Default | What it decides |
|---|---|---|---|
| The key | string | | The entity ID of the identity provider, compared exactly with the one of its metadata, and never an entity ID of the tenant |
| `metadata` | string, not empty | required | Where its metadata are read from: an `https` URL, no redirect followed, or the absolute path of a file of the deployment |
| `metadata_signers` | list of strings | none | The certificates its metadata are signed by, each the base64 of its DER, sixteen at most. Named, the metadata are verified under them and carry a `validUntil` |
| `domains` | list of strings | required | The e-mail domains it answers for, one at least and 256 at most: each the whole part of an address after its `@`, read without regard to case, a name outside ASCII written as its A-label. A domain answers to one identity provider of the tenant |
| `email_attribute` | string, not empty | required | The attribute that carries the e-mail address of a person |
| `profile` | map of attribute to claim | none | The attributes that fill the profile of a person, each naming the claim it fills, one attribute per claim, among the claims a person can describe themselves with |
| `subject_attribute` | string | none | The attribute that names a person when the `NameID` of an assertion is not persistent: a value the identity provider keeps for that person, and never `email_attribute`. Left out, a person is named by a persistent `NameID` only |
| `require_encrypted_assertions` | boolean | `false` | An assertion arrives encrypted for the key the tenant keeps for this identity provider, or it is refused |
| `address_parameter` | string | none | The query parameter of its single sign-on service that takes the address a person typed, `login_hint` for Microsoft Entra ID: one to 64 unreserved characters of RFC 3986, and none of the parameters of the binding. Left out, no address is sent |
| `groups.attribute` | string, not empty | required in the block | The attribute that carries the groups of a person |
| `groups.map` | map of value to group name | none | The group of the tenant each value of that attribute stands for, compared exactly, 256 values at most. A value the map does not name is no group, and no group is ever created from one |
