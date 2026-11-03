---
title: Your first client
description: Registering a client with an initial access token, what it sends, and what the provider refuses.
---

# Your first client

A client is an application the provider answers. It has an identifier, a way of authenticating itself, and
the exact addresses it may be sent back to.

## Registering one

A client reaches the application by registering itself (RFC 7591), and in no other way: the image declares
no client, and until its deployment names how a client is authorised to register, it serves no registration
endpoint. For the clients of an organisation, what authorises one is an initial access token the tenant
issues to the team that integrates:

``` dotenv
BEFFROI_REGISTRATION_MODE=initial_access_token
```

The token is issued in a container of the image:

``` bash
bin/console beffroi:client:token:issue 'My application'
```

The command prints the token once, and the provider keeps its SHA-256 and never the value. It is worth one
registration and thirty days unless `--registrations` and `--days` say otherwise. The team registers its
client with it:

``` http
POST /register HTTP/1.1
Host: op.example.com
Content-Type: application/json
Authorization: Bearer 0NM8Z6ijkVrFDzEaMPwCLWmTvdFxNsRwBCzu8UxS4pQ

{
    "client_name": "My application",
    "redirect_uris": ["https://app.example.com/oidc/callback"],
    "post_logout_redirect_uris": ["https://app.example.com/"],
    "token_endpoint_auth_method": "client_secret_basic",
    "scope": "openid profile email"
}
```

| Field | What it means |
|---|---|
| `client_name` | What a person reads on the consent page. It is the name of a stranger until you set it |
| `redirect_uris` | The addresses the browser may be sent back to, compared exactly. One entry per address, no pattern |
| `post_logout_redirect_uris` | Where the browser may be sent after a logout, compared the same way |
| `token_endpoint_auth_method` | The one method this client authenticates with. A client authenticates with the method it registered and no other, RFC 6749 §2.3.1 |
| `scope` | The ceiling of what this client may ask for, among the scopes the tenant hands out. Asking for more is refused, asking for less is normal |

The answer carries the `client_id` the provider drew and, for a method that proves a secret such as
`client_secret_basic`, the `client_secret`. It also carries a registration access token, with which the
client reads, replaces and deletes its own registration at the `registration_client_uri` the answer names.

[:beffroi-arrow-right: Dynamic registration, in full](../oidc/dynamic-registration.md)

## A public client

A client that cannot keep a secret does not get one: it registers `token_endpoint_auth_method: none`, and the
answer carries no secret. PKCE is what protects it, and a public client cannot be exempted from it.

``` json
{
    "client_name": "My desktop application",
    "redirect_uris": ["http://127.0.0.1/oidc/callback"],
    "token_endpoint_auth_method": "none",
    "scope": "openid profile"
}
```

A native application receives its code on the loopback interface, named by its IP literal, `127.0.0.1` or
`[::1]`, and never by a name (RFC 8252 §8.3), on whatever port it opened: for a public client, a loopback
redirect URI is the one comparison that ignores the port (RFC 8252 §7.3). A custom URI scheme is refused
(RFC 8252 §7.1), so a mobile application registers an `https` URI it claims (RFC 8252 §7.2).

## What the provider refuses

- A redirect URI that is not in the list, even by one character, even by a trailing slash. The one
  difference accepted is the port of a loopback URI registered by a public client, above.
- An authorization request with `code_challenge_method=plain`, always, and one without `code_challenge`. The
  configuration of a tenant can exempt confidential clients from PKCE, and the image exempts none; a public
  client cannot be exempted.
- A client authenticating with a method other than the one it registered.
- A scope the client was not granted.

## Reading what exists

``` bash
bin/console beffroi:client:list
bin/console beffroi:client:show s6Bh3dRkqt3Hm9vBkrnfeR7_xU2ZyQ4lJaN0cP8TwYg
```

The listing covers every client of the tenant, each saying whether it registered itself or the configuration
declares it: the image declares none, and the development stack declares the clients of the conformance suite
and of the demonstrations. A client that registered itself can be deleted with `beffroi:client:delete`; one
the configuration declares cannot, because the configuration would put it back.

[:beffroi-arrow-right: Clients, in full](../oidc/clients.md) and
[client authentication](../oidc/client-authentication.md)
