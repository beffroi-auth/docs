---
title: Your first client
description: Declaring a client in the configuration, what each field means, and what the provider refuses.
---

# Your first client

A client is an application the provider answers. It has an identifier, a way of authenticating itself, and
the exact addresses it may be sent back to.

!!! note "With the image of the standalone application"

    The image declares no client and reads none from its environment: a client registers itself (RFC 7591 §3).
    With `BEFFROI_REGISTRATION_MODE=initial_access_token`, the console issues the token the client presents,
    printed once:

    ``` bash
    bin/console beffroi:client:token:issue 'My application' --registrations=1 --days=1
    ```

    The client then posts the fields below to `/register` in JSON, the secret aside, which the provider
    issues: [dynamic registration](../oidc/dynamic-registration.md).

## Declaring one

Clients a Symfony application knows in advance are declared in its configuration. The key is the `client_id`.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        my-application:
            client_name: 'My application'
            secret: '%env(MY_APPLICATION_SECRET)%'
            redirect_uris: ['https://app.example.com/oidc/callback']
            post_logout_redirect_uris: ['https://app.example.com/']
            token_endpoint_auth_method: client_secret_basic
            scope: 'openid profile email offline_access'
```

| Field | What it means |
|---|---|
| `client_name` | What a person reads on the consent page. It is the name of a stranger until you set it |
| `secret` | Never written in the file. An environment variable, and only for a confidential client |
| `redirect_uris` | The addresses the browser may be sent back to, compared exactly. One entry per address, no pattern |
| `post_logout_redirect_uris` | Where the browser may be sent after a logout, compared the same way |
| `token_endpoint_auth_method` | The one method this client authenticates with. A client authenticates with the method it registered and no other, RFC 6749 §2.3.1 |
| `scope` | The ceiling of what this client may ask for. Asking for more is refused, asking for less is normal |

## A public client

A client that cannot keep a secret does not get one: no `secret`, and `token_endpoint_auth_method: none`.
PKCE is what protects it, and a public client cannot be exempted from it.

``` yaml
beffroi:
    clients:
        my-desktop-application:
            client_name: 'My desktop application'
            redirect_uris: ['http://127.0.0.1/oidc/callback']
            token_endpoint_auth_method: none
            scope: 'openid profile offline_access'
```

A native application receives its code on the loopback interface, named by its IP literal, `127.0.0.1` or
`[::1]`, and never by a name (RFC 8252 §8.3), on whatever port it opened: for a public client, a loopback
redirect URI is the one comparison that ignores the port (RFC 8252 §7.3). A custom URI scheme is refused
(RFC 8252 §7.1), so a mobile application registers an `https` URI it claims (RFC 8252 §7.2).

## What the provider refuses

- A redirect URI that is not in the list, even by one character, even by a trailing slash. The one
  difference accepted is the port of a loopback URI registered by a public client, above.
- An authorization request with `code_challenge_method=plain`, always, and one without `code_challenge`,
  unless the client is a confidential one registered with `requires_pkce: false`. A public client cannot
  be.
- A client authenticating with a method other than the one it registered.
- A scope the client was not granted.

## Reading what exists

``` bash
bin/console beffroi:client:list
bin/console beffroi:client:show my-application
```

The listing covers every client of the tenant, the ones the configuration declared and the ones that
registered themselves, each saying which it is. A client that registered itself can be deleted with
`beffroi:client:delete`; one the configuration declares cannot, because the configuration would put it
back.

[:beffroi-arrow-right: Clients, in full](../oidc/clients.md) and
[client authentication](../oidc/client-authentication.md)
