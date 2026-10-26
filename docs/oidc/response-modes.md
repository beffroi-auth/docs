---
title: Response modes
description: How the answer of the authorization endpoint travels back to the client: in the query, in a form the browser posts, or as a JWT the tenant signs and may encrypt.
---

# Response modes

The response mode decides how the answer of the authorization endpoint reaches the redirect URI (OAuth 2.0
Multiple Response Type Encoding Practices §2.1): in the query, in a form the browser posts (`form_post`), or
gathered in a JWT the tenant signs and may encrypt for the client (JARM §2.1). A refusal travels the way a
code does. Whatever the mode, the one response type is `code`: `response_types_supported` is `["code"]`, and a
request asking for anything else is refused with `unsupported_response_type`.

| `response_mode` | How the answer travels |
|---|---|
| `query` | In the query of the redirect URI, the browser sent there with a `302`. The default for `code` (RFC 6749 §4.1.2) |
| `form_post` | In a page whose form the browser posts to the redirect URI (OAuth 2.0 Form Post Response Mode §2) |
| `query.jwt` | One `response` parameter in the query, a JWT the tenant signed (JARM §2.1) |
| `form_post.jwt` | One `response` field of the posted form, the same JWT |
| `jwt` | No delivery of its own: it names the signed mode of the response type, `query.jwt` for `code` |

`response_modes_supported` lists the modes the provider is wired with, the four above in that order, and
`jwt` after them because a signed mode is wired. What is wired is what a request may ask for and what the
document announces: a mode is a class the bundle tags, and a deployment that wires fewer announces and serves
fewer.

## Choosing one

A request names its mode in `response_mode`. The mode is read with the redirect URI, before anything else of
the request is judged, because it says how anything reaches the client, a refusal as well as a code (OIDC
Core §3.1.2.6). A mode the provider does not serve is refused with `unsupported_response_mode`, and that
refusal travels in `query`, the mode the provider falls back on to say it. A request that names no mode is
answered in `query`.

The mode inside a [request object](request-objects.md) or a [pushed request](pushed-authorization-requests.md)
is the mode, as any other parameter of it is.

## The query

The parameters are added to the query the redirect URI already has, every value percent-encoded (RFC 3986
§2.1), and the browser is sent there:

``` http
HTTP/1.1 302 Found
Location: https://billing.example.com/oidc/callback?code=SplxlOBeZQQYbYS6WxSbIA0g2Wn7KcHtdUYvSYn4Ls8&state=af0ifjsldkj&iss=https%3A%2F%2Fop.example.com
```

## The form post

The answer is a page holding one form, whose hidden fields are the parameters, posted by the browser to the
redirect URI, so that no parameter of the answer is written in a URL, an address bar, a history or an access
log. One script submits the form as soon as the page loads. The page also says "Your browser is sending you
back to the application. If nothing happens, use the button below." beside a Continue button, which is what a
browser that runs no script shows.

The page carries a policy of its own, under which nothing loads and nothing frames it:

``` http
Content-Security-Policy: default-src 'none'; script-src 'sha256-8lDeP0UDwCO6/RhblgeH/ctdBzjVpJxrXizsnIk3cEQ='; form-action https://billing.example.com; base-uri 'none'; frame-ancestors 'none'
```

`script-src` names the one script by its hash and allows no other script, and `form-action` the origin of the
redirect URI and nothing else. The page is `form_post.html.twig`, which an application overrides under
`templates/bundles/BeffroiBundle/`: it extends no layout, since a stylesheet or a script a layout brings would
be blocked by that policy, and the script stays exactly as the bundle gives it, its hash being the policy. Like
every page of the interaction plane, it is answered with `Cache-Control: no-store` and `Referrer-Policy:
no-referrer`.

The form reaches the redirect URI as a `POST` made from the provider's origin, and a browser does not send a
cookie of the client set `SameSite=Lax` with a `POST` another site makes it send (RFC 6265bis); what the
answer says travels in the posted fields, `state` among them. The provider meets the same rule the other way
round, when a client posts a form to `/authorize`, and posts it again from its own origin ([authorization
request](authorization-request.md)).

## A signed answer

`query.jwt` and `form_post.jwt` gather the answer in one document the tenant signs (JARM §2.1), so that a
client can prove the answer came from this provider and was not rewritten on the way. The document is sent
alone, as `response`; `state` and `iss` travel inside it and nowhere else.

| Claim | What it is |
|---|---|
| The parameters of the answer | `code`, `state` and `iss`, or `error`, `error_description`, `state` and `iss`, each one a claim |
| `iss` | The issuer of the tenant |
| `aud` | The `client_id` |
| `exp` | Five minutes after the answer: a response is read when the browser hands it over |

A refusal is the same document with `error` among its claims (JARM §2.4): a client that asked for
`query.jwt`, `form_post.jwt` or `jwt` never reads an unsigned answer, from the second stage of the request
on. A signed mode the provider does not serve, `fragment.jwt` among them, is refused as any mode it does not
serve is, with `unsupported_response_mode` in `query`, unsigned. A refusal of the first stage, before the
redirect URI is known, is a page and reaches no client in any mode.

The document is signed with the active key of the tenant, in the algorithm the client registered in
`authorization_signed_response_alg`, or in `RS256`, the first the provider is wired with, when it registered
none (JARM §3); it carries no `typ`. A client that registered `authorization_encrypted_response_alg` and
`authorization_encrypted_response_enc` receives it inside a JWE addressed to one of its keys, signed first and
encrypted second ([encryption](tokens/encryption.md)).

The discovery document announces `authorization_signing_alg_values_supported`, the algorithms the provider
signs with, `authorization_encryption_alg_values_supported` and `authorization_encryption_enc_values_supported`,
the ones it encrypts to a client with, and the `jwt` alias, all of them only because a signed mode is wired.

[:beffroi-arrow-right: Authorization request](authorization-request.md) and [request
objects](request-objects.md)
