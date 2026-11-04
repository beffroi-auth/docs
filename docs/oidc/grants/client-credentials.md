---
title: Client credentials
description: A service asking for a token for itself, RFC 6749 §4.4, what it has to name, what the token says, and what a resource server reads of it.
---

# Client credentials

In the client credentials grant (RFC 6749 §4.4) there is nobody behind the request: a confidential client
asks for an access token for itself, to call a resource it names. Nobody is asked, so there is no consent;
nobody signed in, so there is no ID token; and the answer carries no refresh token (§4.4.3), the client
asking again when it needs a new one.

## Registering a service

A service reaches a deployment of the image by [registering itself](../dynamic-registration.md). The
deployment opens registration, and names the scopes of the API the service calls, which the tenant then hands
out ([configuration](../../application/configuration.md#the-tenant)):

``` dotenv
BEFFROI_REGISTRATION_MODE=initial_access_token
BEFFROI_TENANT_SCOPES='["invoices.read","invoices.write"]'
```

The service registers with:

``` json
{
    "client_name": "Billing service",
    "token_endpoint_auth_method": "client_secret_basic",
    "grant_types": ["client_credentials"],
    "scope": "invoices.read invoices.write"
}
```

The answer carries the `client_id` the provider drew and the `client_secret`, said once.

| Member | What it decides here |
|---|---|
| `token_endpoint_auth_method` | Any method that proves something. `none` is refused for a client registered for this grant |
| The `client_id` | The `sub` of every token this grant issues the client, so it is one to 255 visible ASCII characters, and no space, which the identifier the provider draws always is |
| `grant_types` | `client_credentials`. A client registered for no grant that sends a browser back to it registers no redirect URI |
| `scope` | The scopes it may ask for. `openid` is refused whatever the registration says, this grant having nobody to authenticate |
| `resources` | *Deployment.* The resources it may ask a token for. A client that registered none can obtain nothing with this grant, a request having to name one |

!!! warning "No token for a client of the image"

    `resources` is a member of the deployment: a registration that carries it is refused, and no variable
    gives it to a client ([what the image does not set](../clients.md#what-the-image-does-not-set)). A client
    of the image therefore registers no resource, and a request it makes with this grant whose scopes hold is
    refused with `invalid_target`, whether it names a resource or not: on a deployment of the image, the
    client credentials grant issues no token. The rest of this page is what the grant does for a client that
    carries resources.

## The request

| Parameter | |
|---|---|
| `grant_type` | `client_credentials` |
| `scope` | Required here, although RFC 6749 §4.4.2 makes it optional: a request that named nothing would otherwise be answered with everything the client is registered for |
| `resource` | Required and repeatable, among the resources the client registered (RFC 8707 §2): a token addressed to the client that asked for it is a token no resource server is meant to accept, and it is the one thing this grant does not hand out |

| Refusal | Error |
|---|---|
| No `scope` | `invalid_request` |
| `openid` among the scopes (OIDC Core §2) | `invalid_scope` |
| A scope the client did not register, or a `scope` that is not a list of scope tokens | `invalid_scope` |
| No `resource` | `invalid_target` |
| A resource the client did not register, or one that is not an absolute URI without a fragment | `invalid_target` |

## What the token says

| Claim | Value |
|---|---|
| `sub` | The `client_id` (RFC 9068 §2.2) |
| `client_id` | The `client_id` |
| `aud` | The resources the request named |
| `scope` | The scopes the request named |
| `grant_id` | An identifier drawn for this answer |
| `cnf` | What the token is bound to, when the request binds one ([grants](index.md#what-the-token-endpoint-does)) |
| `may_act` | Who may act for the subject of a token of this client, in the self-contained shape, when it carries `may_act`, a member of the deployment |

There is no `sid`, `auth_time`, `acr` or `amr`, nobody having signed in, and no `person`, the token being
about nobody. The answer is the access token, its `token_type`, `expires_in` and `scope`, and nothing else.
[Access tokens](../tokens/access-tokens.md) has every claim of either shape.

## What a resource server reads

- **A self-contained token** is verified offline, as every `at+jwt` is: its `sub` is the client, and nothing in
  it describes a person.
- **An opaque token** is introspected by the client it was issued to, the introspection endpoint describing a
  token to that client and to nobody else (RFC 7662 §2.2). The answer renders the same members, and the same
  absence of the members of a sign-in.
- **No end of a session and no consent taken back reach it**: it descends from neither. The client takes an
  opaque one back at the revocation endpoint, and a self-contained one lives `BEFFROI_ACCESS_TOKEN_TTL`, ten
  minutes in the image.
- **The UserInfo endpoint does not answer it**: the token names nobody, and it is addressed to a resource
  rather than to the provider.
