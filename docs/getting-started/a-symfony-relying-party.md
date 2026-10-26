---
title: A Symfony relying party
description: Signing people in to a Symfony application with the oidc_login authenticator, signing them out again, and checking the access token on a resource server.
---

# A Symfony relying party

The client of reference for this provider is Symfony's own `oidc_login` authenticator, which Symfony 8.2 adds
with an `oidc` user provider: what Beffroi emits is played against it, with no patch of the authenticator.
That makes a Symfony application the shortest path to a sign-in you can watch end to end, and it takes two
halves: a client declared on the provider, and a firewall in the application.

## On the provider

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        my-application:
            client_name: 'My application'
            secret: '%env(MY_APPLICATION_SECRET)%'
            redirect_uris: ['https://app.example.com/oidc/callback']
            post_logout_redirect_uris: ['https://app.example.com/']
            token_endpoint_auth_method: client_secret_basic
```

`/oidc/callback` is the path `oidc_login` is called back on unless told otherwise, and `/` the one it sends a
browser to after a logout; both are compared exactly. What the declaration leaves out takes the defaults this
application needs: the scopes `openid profile email`, the authorization code grant and its renewal by a refresh
token, access tokens in the `at+jwt` shape (RFC 9068), and a consent asked of each person the first time. The
secret is at least 32 visible ASCII characters, generated.

[:beffroi-arrow-right: Your first client](your-first-client.md)

## In the application

The authenticator needs the HTTP client of Symfony to reach the provider, and `web-token/jwt-library` to
verify what it signed:

``` bash
composer require symfony/security-bundle symfony/http-client web-token/jwt-library
```

``` yaml title="config/packages/security.yaml"
security:
    providers:
        oidc:
            oidc: ~

    firewalls:
        main:
            lazy: true
            oidc_login:
                provider_uri: '%env(OIDC_PROVIDER_URI)%'
                client_id: '%env(OIDC_CLIENT_ID)%'
                client_authentication:
                    client_secret_basic: '%env(OIDC_CLIENT_SECRET)%'
                scope: ['openid', 'profile', 'email']
                refresh_access_token: true
                enable_end_session: true
            logout: true

    access_control:
        - { path: ^/profile, roles: ROLE_USER }
```

The routes of the firewall, the callback and the logout among them, are declared by one route loader, which
the application imports:

``` yaml title="config/routes/security.yaml"
_security:
    resource: security.route_loader
    type: service
```

``` bash title=".env.local"
OIDC_PROVIDER_URI=https://op.example.com
OIDC_CLIENT_ID=my-application
OIDC_CLIENT_SECRET=
```

`OIDC_PROVIDER_URI` is the issuer, exactly as the provider announces it: the authenticator reads everything
else from its discovery document. A visit to `/profile` without a session sends the browser to the
authorization endpoint of the provider, which signs the person in, asks for their consent the first time, and
sends the browser back to `/oidc/callback` with a code. The user of the firewall is an `OidcUser` built from the
claims UserInfo answers with, holding `ROLE_USER`.

### What the two sides agree on without being told

| `oidc_login` | Beffroi |
|---|---|
| Sends PKCE with `S256` unless told otherwise | Refuses an authorization request without it, and never takes `plain` |
| Accepts an ID token signed with `RS256` unless `id_token_signature.algorithms` names others | Signs with `RS256`, the first algorithm it is wired with, unless the client registers another `id_token_signed_response_alg` |
| Reads the claims from UserInfo unless `user_data_source` says otherwise | Answers UserInfo with the claims of the scopes the person agreed to (OIDC Core §5.3) |
| Renews the access token with the refresh token, with `refresh_access_token` | Issues a refresh token to a confidential client registered for the refresh token grant, `offline_access` asked for or not, and to a public one that asks for `offline_access` |
| Sends the scopes of `scope` | Takes the scopes the client registered and refuses any other with `invalid_scope` |

**The refresh token of this client stands.** A confidential client is told from a copy of its token by its
own authentication, so Beffroi answers a renewal with a new access token and no new refresh token, and the
one the application holds works until it expires, thirty days after it was issued by default. Only the
refresh token of a public client bound to no key or certificate is rotated at every use (RFC 9700 §4.13.2):
its successor comes with the response, and the rotated token presented again revokes its whole family. For
such a client, two requests of one browser renewing the same token at once would be that replay; a session
handler that locks the session keeps them apart, and the default one of Symfony does.

## Signing out

**`enable_end_session`** is RP-Initiated Logout 1.0: the `/logout` of the firewall sends the browser to the
end session endpoint of the provider, with the ID token as `id_token_hint` and the absolute URL of
`post_logout_redirect_path`, `/` unless told otherwise, as `post_logout_redirect_uri`. The provider ends its
session, which revokes what was issued under it, and sends the browser back to that URL. It has to be one of
the `post_logout_redirect_uris` of the client: any other is refused with `invalid_request`, and no error of
that endpoint is a redirection.

**The back channel** tells the application when the session of the provider ends anywhere else: at the end
session endpoint through another client, from the account of the person, by the console. The provider posts a
logout token to the client (Back-Channel Logout 1.0 §2.5), and the firewall ends the local session it opened
under it.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        my-application:
            # ...
            backchannel_logout_uri: 'https://app.example.com/oidc/backchannel-logout'
            backchannel_logout_session_required: true
```

``` yaml title="config/packages/security.yaml"
security:
    firewalls:
        main:
            oidc_login:
                # ...
                backchannel_logout:
                    enabled: true
                    cache: cache.app
```

`/oidc/backchannel-logout` is the path the route loader declares for it, `POST` only. The pool `cache` names
remembers the ended sessions, for a day unless `lifetime` says otherwise, and has to be shared by every server
of the application. The logout token is posted by the worker of the provider, so the application answers that
URI where the worker can reach it, over HTTPS, or over plain HTTP on a loopback host.

## A resource server

An `access_token` firewall checks the access token a request carries, in one of two ways.

=== "An at+jwt, verified where it arrives"

    ``` yaml title="config/packages/security.yaml"
    security:
        firewalls:
            api:
                pattern: ^/api/
                stateless: true
                access_token:
                    token_handler:
                        oidc:
                            discovery:
                                base_uri: '%env(OIDC_PROVIDER_URI)%'
                                cache:
                                    id: cache.app
                            issuers: ['%env(OIDC_PROVIDER_URI)%']
                            audience: '%env(OIDC_CLIENT_ID)%'
                            enforce_at_jwt_type: true
    ```

    The discovery document and the keys of the JWK Set it names are kept in the pool `discovery.cache.id`
    names, and the token is accepted from the issuers `issuers` lists. Beffroi signs every access token with
    `RS256`, which is what the handler accepts unless told otherwise, and types it `at+jwt` (RFC 9068 §2.1),
    which `enforce_at_jwt_type` holds it to.

    The `aud` of the token is the client it was issued to, unless the client asked for a resource (RFC 8707
    §2), in which case it names that resource and the `audience` of the handler is that identifier. Nothing
    reaches the provider: a token revoked there is accepted here until it expires, ten minutes after it was
    issued by default.

=== "Any token, described by the provider"

    ``` yaml title="config/packages/framework.yaml"
    framework:
        http_client:
            scoped_clients:
                introspection.client:
                    base_uri: '%env(OIDC_INTROSPECTION_URI)%'
                    auth_basic: '%env(OIDC_CLIENT_ID)%:%env(OIDC_CLIENT_SECRET)%'
    ```

    ``` yaml title="config/packages/security.yaml"
    security:
        firewalls:
            api:
                pattern: ^/api/
                stateless: true
                access_token:
                    token_handler:
                        oauth2:
                            http_client: introspection.client
                            issuer: '%env(OIDC_PROVIDER_URI)%'
                            audience: '%env(OIDC_CLIENT_ID)%'
    ```

    `OIDC_INTROSPECTION_URI` is the issuer followed by `/introspect`. The provider describes a token to the
    client it was issued to and to nobody else (RFC 7662 §2.2), so the resource server asks with the
    credentials of that client, and an opaque access token, `access_token_format: opaque` on the client, is
    read this way only. A token whose session has ended, or whose grant was taken back, is described as
    inactive from then on; a `cache` on the handler keeps an active answer for up to sixty seconds, never past
    the `exp` of the token.

    Beffroi reads both halves of HTTP Basic credentials form-urlencoded, as RFC 6749 §2.3.1 writes them and
    as `oidc_login` sends them, while the scoped client sends `auth_basic` as it is given. A secret drawn in
    base64url reads the same both ways; one holding a `+`, a `%` or a colon is encoded in the variable the
    scoped client reads.

Either way, what a route needs is a scope, which Symfony reads from the `scope` of the token or of the answer:

``` yaml title="config/packages/security.yaml"
security:
    access_control:
        - { path: ^/api/invoices, roles: 'OAUTH2_SCOPE(invoices.read)' }
```

A token without it is refused with `403` and the `insufficient_scope` challenge of RFC 6750 §3.1. A scope that
stands for no claim, `invoices.read` here, exists on the provider once a client registers it in its `scope`,
and the application asks for it in its own.

## The reference relying party

[beffroi-auth/oidc-demo](https://github.com/beffroi-auth/oidc-demo) is this page grown into everything the
provider serves: a Symfony application on `oidc_login`, a resource server that checks the same access token
several ways, an API Platform API behind the introspection endpoint where every operation names the scope it
needs, and a forge where a client is composed option by option out of what the provider announces and
registered on the spot, from one that puts the whole authorization request in the URL of a browser to one that
pushes it signed, reads a signed response, holds a bound token and opens an encrypted ID token.

From a working copy of the monorepo with oidc-demo checked out beside it, `castor demo` points it at
[the development stack](the-standalone-application.md#on-your-machine) and starts it on
`https://localhost:8002`, and `castor demo --check` signs in as the development user, opens `/profile` and
signs out, from the command line.
