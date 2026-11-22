---
title: Add sign-in to a Symfony application
description: Let people sign in to your Symfony application with Beffroi OP, using the oidc_login authenticator of Symfony, sign them out, and protect an API with the access token.
---

# Add sign-in to a Symfony application

This guide adds sign-in with Beffroi OP to a Symfony application. It uses `oidc_login`, the authenticator
Symfony 8.2 ships with its `oidc` user provider, and nothing else: no package of Beffroi is installed in your
application.

When you are done, a visitor of a protected page is sent to Beffroi to sign in, comes back signed in, and can
sign out again. The last part of the guide protects an API with the access token Beffroi issues.

!!! info "The client of reference"

    `oidc_login` is the client Beffroi is played against: what the provider emits is checked with this
    authenticator, with no patch of it.

## What you need

- A Beffroi OP served over HTTPS, and access to its console (`bin/console`).
- A Symfony 8.2 or higher application.
- The address of your application, for instance `https://app.example.com`.

## 1. Register your application in Beffroi

Your application registers itself as a client of Beffroi, with a one-time token you issue on the provider.

1. Allow registration with a token: set `BEFFROI_REGISTRATION_MODE=initial_access_token` in the environment of
   the provider.
2. Issue a token that allows one registration:

    ``` bash
    bin/console beffroi:client:token:issue 'My application' --registrations=1 --days=30
    ```

    The token is printed once. Copy it.

3. Register the application with that token:

    ``` bash
    curl -X POST https://op.example.com/register \
      -H "Authorization: Bearer $INITIAL_ACCESS_TOKEN" -H 'Content-Type: application/json' \
      -d '{
        "client_name": "My application",
        "redirect_uris": ["https://app.example.com/oidc/callback"],
        "post_logout_redirect_uris": ["https://app.example.com/"],
        "grant_types": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_method": "client_secret_basic",
        "scope": "openid profile email"
      }'
    # the answer carries client_id and client_secret, shown once
    ```

    A refused registration spends the token as well. Issue a new one before trying again.

4. Keep the `client_id` and the `client_secret` of the answer. The secret is never shown again.

A few values of this request matter:

- **`redirect_uris`**: `/oidc/callback` is the path `oidc_login` comes back to by default. It is compared
  exactly.
- **`post_logout_redirect_uris`**: `/` is where `oidc_login` sends people after signing out by default. It is
  compared exactly too.
- **`grant_types`** and **`scope`**: a registration that leaves them out gets the authorization code alone and
  the scope `openid` alone. This request names the refresh token and the scopes the application asks for.

Beffroi asks each person for their consent the first time. It deletes a client that registered itself when
nobody uses it for ninety days, or within seven days when it is never used.

[:beffroi-arrow-right: Your first client](your-first-client.md) and
[dynamic registration, in detail](../oidc/dynamic-registration.md)

## 2. Install the packages

``` bash
composer require symfony/security-bundle symfony/http-client web-token/jwt-library
```

The authenticator reaches Beffroi with the HTTP client, and checks what Beffroi signed with
`web-token/jwt-library`.

## 3. Configure the firewall

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

Import the routes of the firewall, the callback and the logout among them:

``` yaml title="config/routes/security.yaml"
_security:
    resource: security.route_loader
    type: service
```

Then fill in the values:

``` bash title=".env.local"
OIDC_PROVIDER_URI=https://op.example.com
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
```

- `OIDC_PROVIDER_URI` is the address of Beffroi, exactly as it announces itself. The authenticator finds
  everything else from there.
- `OIDC_CLIENT_ID` and `OIDC_CLIENT_SECRET` are the `client_id` and the `client_secret` of the answer to the
  registration.

## 4. Try it

1. Open `https://app.example.com/profile`. You are not signed in, so your browser goes to Beffroi.
2. Sign in. The first time, Beffroi asks you to agree to share your profile and email address with the
   application.
3. Beffroi sends you back to `/oidc/callback`, and Symfony shows `/profile`. Its user is an `OidcUser` built
   from what Beffroi shared, with the role `ROLE_USER`.

## Sign out

With `enable_end_session`, the `/logout` of the firewall signs the person out of Beffroi too. Beffroi ends its
session, revokes every token issued under it, and sends the browser back to `/`. An API that checks the access
token locally still accepts it until it expires. The address `/` has to be one of the
`post_logout_redirect_uris` of the client, or Beffroi refuses the sign-out.

### When the person signs out elsewhere

A person can also end their session on Beffroi from another application, from their account, or from the
console. To end the session of your application at the same time, let Beffroi tell it. Add two members to the
registration of step 1:

``` json
{
    "backchannel_logout_uri": "https://app.example.com/oidc/backchannel-logout",
    "backchannel_logout_session_required": true
}
```

A client already registered adds them by replacing its registration
([reading, replacing and deleting itself](../oidc/dynamic-registration.md#reading-replacing-and-deleting-itself)).
Then turn it on in the firewall:

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

- `/oidc/backchannel-logout` is declared by the route loader you imported, `POST` only.
- The `cache` pool remembers the ended sessions, for a day by default. Every server of your application has to
  share it.
- The worker of Beffroi is what calls that address. It must reach it over HTTPS, or over plain HTTP on a
  loopback host.

[:beffroi-arrow-right: Logout](../oidc/logout.md)

## Protect an API

An `access_token` firewall checks the access token a request carries. Choose one of two ways.

=== "Check the token locally"

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

    Your API checks the signature of the token with the keys Beffroi publishes, and never calls Beffroi for a
    request. Beffroi signs access tokens with `RS256` and types them `at+jwt` (RFC 9068 §2.1), which this handler
    expects.

    - `audience` is the `client_id` of the client the token was issued to. A client whose initial access token
      granted it a resource (RFC 8707 §2), with `--resource`, and that asks for it, gets a token addressed to that
      resource instead.
    - A token revoked on Beffroi is still accepted here until it expires, ten minutes after it was issued by
      default.

=== "Ask Beffroi about the token"

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

    Your API asks Beffroi about each token, at the introspection endpoint (RFC 7662 §2).
    `OIDC_INTROSPECTION_URI` is the address of Beffroi followed by `/introspect`.

    - Beffroi describes a token only to the client it was issued to (RFC 7662 §2.2), so the API asks with the
      credentials of that client.
    - A token whose session ended, or whose authorization was taken back, is answered as inactive at once. A
      `cache` on the handler keeps an active answer for up to sixty seconds, never past the expiry of the token.
    - This is the only way to accept opaque access tokens, which a client receives when the initial access token
      it registered with was issued with `--access-token-format opaque`.
    - The secret Beffroi draws at registration is base64url, and goes in the variable as it is. Beffroi reads
      both halves of the credentials form-urlencoded (RFC 6749 §2.3.1), so a secret with a `+` or a `%` would
      have to be encoded.

Then require a scope on each route:

``` yaml title="config/packages/security.yaml"
security:
    access_control:
        - { path: ^/api/invoices, roles: 'OAUTH2_SCOPE(invoices.read)' }
```

A token without that scope is refused with `403` and `insufficient_scope`. A scope of your own, such as
`invoices.read`, is one Beffroi hands out once its deployment names it, the client registers it in its
`scope`, and the application asks for it:

``` dotenv
BEFFROI_TENANT_SCOPES='["invoices.read"]'
```

## How it works

You do not need this section to follow the guide. It lists what `oidc_login` and Beffroi do without being told.

| `oidc_login` | Beffroi |
|---|---|
| Protects the sign-in with PKCE, `S256` by default | Requires PKCE, and accepts `S256` only |
| Accepts an ID token signed with `RS256` unless `id_token_signature.algorithms` names others | Signs with `RS256` unless the client registers another `id_token_signed_response_alg` |
| Reads who the person is from the UserInfo endpoint, unless `user_data_source` says otherwise | Answers UserInfo with what the person agreed to share |
| Renews the access token with the refresh token, with `refresh_access_token` | Issues a refresh token to this client whether it asks for `offline_access` or not |
| Asks for the scopes of `scope` | Accepts the scopes the client registered, and refuses any other with `invalid_scope` |

**The refresh token of this client does not change.** Your application proves who it is with its secret at
every renewal, so Beffroi answers with a new access token and keeps the refresh token as it is. It works until
thirty days after it was issued, by default. Only the refresh token of a public client bound to no key or
certificate is replaced at every use, and presenting a replaced one again revokes all of them. For such a
client, two renewals at once from one browser would look like that replay; the default session handler of
Symfony locks the session and keeps them apart.

[:beffroi-arrow-right: Refresh tokens](../oidc/tokens/refresh-tokens.md)

## The reference application

[beffroi-auth/oidc-demo](https://github.com/beffroi-auth/oidc-demo) is this guide grown into everything Beffroi
serves. It is a Symfony application on `oidc_login`, laid out as a tree of the features of the provider,
grouped: signing in, client authentication, tokens, protecting an API, documents, signing out, the grants that
need no browser, and FAPI 2.0. Each feature faces a client, shows the configuration of that client, runs it
against the provider and shows what travelled. Around the tree:

- an API Platform API that verifies an access token addressed to it on its own (RFC 8707 §2, RFC 9068) and
  asks Beffroi about any other (RFC 7662), whose Swagger UI signs in with the authorization code and PKCE as a
  public client;
- routes that check the access token of the session several ways: introspected, introspected with a signed
  answer, verified offline, and bound by DPoP;
- a page where you compose a client option by option and register it on the spot (RFC 7591).

From a working copy of the monorepo with oidc-demo checked out beside it, `castor demo` points it at
[the development stack](the-standalone-application.md#on-your-machine) and starts it on
`https://localhost:8002`. `castor demo --check` signs in as the development user, opens `/profile` and signs
out, from the command line.
