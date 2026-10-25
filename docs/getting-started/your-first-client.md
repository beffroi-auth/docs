---
title: Your first client
description: Declaring a client in the configuration, what each field means, and what the provider refuses.
---

# Your first client

A client is an application the provider answers. It has an identifier, a way of authenticating itself, and
the exact addresses it may be sent back to.

## Declaring one

Clients a deployment knows in advance are declared in the configuration. The key is the `client_id`.

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
PKCE is what protects it, and PKCE is mandatory here anyway.

``` yaml
beffroi:
    clients:
        my-mobile-application:
            client_name: 'My mobile application'
            redirect_uris: ['com.example.app:/oidc/callback']
            token_endpoint_auth_method: none
            scope: 'openid profile offline_access'
```

## What the provider refuses

- A redirect URI that is not in the list, even by one character, even by a trailing slash.
- An authorization request without `code_challenge`, or with `code_challenge_method=plain`.
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
