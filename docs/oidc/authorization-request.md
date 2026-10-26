---
title: Authorization request
description: What the authorization endpoint reads, the order it judges a request in, and which refusals go back to the client rather than to the person.
---

# Authorization request

The authorization endpoint, `/authorize`, reads a request in the query of a `GET` or in the form of a `POST`
(OIDC Core §3.1.2.1). It finds the client, compares the redirect URI exactly, requires PKCE with `S256`, and
hands what is left to an [interaction](interactions.md), which decides whether a person has to be shown a
page at all. Every answer that reaches the client, a code or a refusal, carries `iss` (RFC 9207 §2), and
`state` when the request carried one.

``` http
GET /authorize?response_type=code
    &client_id=billing
    &redirect_uri=https%3A%2F%2Fbilling.example.com%2Foidc%2Fcallback
    &scope=openid%20profile%20email
    &state=af0ifjsldkj
    &nonce=n-0S6_WzA2Mj
    &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
    &code_challenge_method=S256 HTTP/1.1
Host: op.example.com
```

## How a request is read

Every parameter is read the same way at every endpoint of the provider (RFC 6749 §3.1): it is one string, a
parameter sent empty is a parameter not sent, a parameter the provider does not read is ignored, and nothing
is converted into anything else. A parameter the provider reads, sent twice in a query or in a body of
`Content-Type: application/x-www-form-urlencoded`, is refused with `invalid_request`, with one exception,
`resource`, which RFC 8707 §2 lets a client send once per resource.

Two kinds of request take their parameters from elsewhere than the query or the form:

- **A pushed request** names, in `request_uri`, a reference the client received from the [pushed
  authorization request endpoint](pushed-authorization-requests.md). The parameters are the ones it pushed,
  and every other parameter the browser carried but `client_id` is dropped.
- **A request object** carries the request in a JWT, by value in `request` or by reference in `request_uri`
  ([request objects](request-objects.md)). The parameters are the claims of the object, and every other
  parameter the browser carried but `client_id` is dropped as well.

Both are resolved before anything else is read, and what either refuses is refused on a page, since what
names the destination is what could not be read.

## The parameters

| Parameter | Required | What it has to be | The error of a refusal |
|---|---|---|---|
| `client_id` | Yes | A client of the tenant | A page |
| `redirect_uri` | Yes | One of the redirect URIs of the client, [byte for byte](#the-redirect-uri) | A page |
| `state` | No | Printable ASCII (RFC 6749 appendix A.5), sent back as it came | A page |
| `response_type` | Yes | `code` | `unsupported_response_type` |
| `response_mode` | No | A mode the provider answers in ([response modes](response-modes.md)) | `unsupported_response_mode` |
| `scope` | Yes | Scope tokens separated by spaces, every one registered by the client, `openid` among them | `invalid_scope` |
| `code_challenge` | Yes, unless the client is [exempted](#pkce) | 43 to 128 unreserved characters (RFC 7636 §4.2) | `invalid_request` |
| `code_challenge_method` | With a challenge | `S256` | `invalid_request` |
| `nonce` | No | Text with no control character, carried into the ID token | `invalid_request` |
| `prompt` | No | `none`, `login`, `consent` and `select_account`, separated by spaces, `none` alone | `invalid_request` |
| `max_age` | No | A number of seconds, `0` or more | `invalid_request` |
| `login_hint` | No | Text with no control character | `invalid_request` |
| `ui_locales` | No | Language tags separated by spaces (RFC 5646) | `invalid_request` |
| `acr_values` | No | Values of visible ASCII separated by spaces | `invalid_request` |
| `display` | No | `page`, `popup`, `touch` or `wap` | `invalid_request` |
| `id_token_hint` | No | An ID token this provider signed, for this client | `invalid_request` |
| `claims` | No | A claims request (OIDC Core §5.5) | `invalid_request` |
| `dpop_jkt` | No | The JWK thumbprint of the key the code is reserved for, a SHA-256 in base64url (RFC 9449 §10) | `invalid_request` |
| `resource` | No, repeatable | An absolute URI without a fragment, registered by the client | `invalid_target` |
| `authorization_details` | No | A JSON array of details of types the client registered | `invalid_authorization_details` |

A required parameter that is missing is `invalid_request`, wherever its line says the refusal goes. What
`prompt`, `max_age`, `login_hint`, `acr_values` and `id_token_hint` ask of the login is on [the page about
interactions](interactions.md), and `claims` on [scopes and claims](scopes-and-claims.md). `ui_locales`
chooses the language of the pages ([translations](../symfony-bundle/translations.md)). `display` is checked and
kept, and no page of the bundle reads it.

## The order of the checks

A request is judged in two stages, because the specification decides when a refusal may go back to the
client (RFC 6749 §4.1.2.1, RFC 9700 §4.1): nothing goes back to a redirect URI that has not been checked yet.
Each stage stops at its first refusal.

1. **Before anything is read.** A form posted from another site without the session cookie is [posted
   again](#a-request-posted-from-another-site), then the pushed request or the request object is resolved.
2. **The first stage, refused on a page.** `client_id`, and the client it names. A client registered with
   `require_pushed_authorization_requests` is refused a request that was not pushed, and one registered with
   `require_signed_request_object` a request that no request object carried, both before the redirect URI
   is read, so that nothing of the request goes back to the browser it came from. Then `redirect_uri`,
   `state`, and the response mode the answer will travel in.
3. **The second stage, refused at the redirect URI.** `response_type`, `response_mode`, then `prompt`,
   `max_age`, `login_hint`, `ui_locales`, `acr_values`, `display`, the form of `id_token_hint`, `claims`, then
   `scope`, the PKCE pair, `nonce`, `dpop_jkt`, `resource` and `authorization_details`.
4. **The interaction, refused at the redirect URI too.** The `id_token_hint` is verified, an essential `acr`
   the provider cannot prove is refused with `unmet_authentication_requirements`, and the login and the
   consent the request needs are asked for ([interactions](interactions.md)).

## PKCE

A request carries a `code_challenge` and `code_challenge_method=S256`, the one method the provider is wired
with and announces in `code_challenge_methods_supported` (RFC 7636 §4.3). `plain` is wired nowhere and
announced nowhere, and a challenge sent without a method is refused rather than read as `plain`, which is
what RFC 7636 §4.3 would make of it.

A confidential client registered with `requires_pkce: false` may send neither parameter; a challenge it does
send is held to the same rules, and the code exchange then verifies it. A public client cannot be registered
so. The token endpoint compares `BASE64URL(SHA256(code_verifier))` with the challenge in constant time
([authorization code](grants/authorization-code.md)).

## The redirect URI

`redirect_uri` is required, and compared byte for byte with the redirect URIs the client registered (RFC 6749
§3.1.2.3): a trailing slash, the case of a letter or a parameter of the query make another URI. The one
exception is the loopback redirection of a public native client, whose port may differ (RFC 8252 §7.3),
which [clients](clients.md) describes. The answer goes to the URI the request named, the parameters added to
the query it already has, and the token request repeats that URI exactly.

## The answer

When nothing more is needed, the browser goes back with a `code`, the `state` of the request when it carried
one, and the `iss` of the tenant:

``` http
HTTP/1.1 302 Found
Location: https://billing.example.com/oidc/callback?code=SplxlOBeZQQYbYS6WxSbIA0g2Wn7KcHtdUYvSYn4Ls8&state=af0ifjsldkj&iss=https%3A%2F%2Fop.example.com
```

That is the `query` mode, the default for `code`; the [response mode](response-modes.md) of the request
decides how the answer travels, and a refusal travels the same way. The code is worth one exchange and lives
60 seconds by default (`tokens.authorization_code_ttl`, 600 at most). A token request spends it as soon as
it finds it, whatever the checks that follow decide, the client the code was issued to, the redirect URI and
the verifier among them ([authorization code](grants/authorization-code.md)).

## Refusals

**On a page.** A refusal of the first stage, of a pushed request or of a request object is never sent to the
redirect URI: the person reads a page, with status `400`, that asks them to start again from the application,
and beneath it the `error` and the `error_description` for whoever develops the application. The page is the
bundle's `error.html.twig`, which an application overrides like the others
([pages](../symfony-bundle/pages.md)).

**At the redirect URI.** Every other refusal goes back to the client, in the mode of the request, with
`error`, `error_description`, `state` and `iss`:

| Error | When |
|---|---|
| `invalid_request` | A parameter missing, repeated or malformed, a challenge missing or not `S256`, an `id_token_hint` that is not an ID token of this provider for this client |
| `invalid_scope` | A scope the client did not register, a malformed list, a list without `openid` |
| `unsupported_response_type` | Anything but `code` |
| `unsupported_response_mode` | A mode the provider does not answer in |
| `invalid_target` | A resource that is not an absolute URI, or that the client did not register |
| `invalid_authorization_details` | A detail of a type the provider does not serve or the client did not register, or that its type refuses |
| `login_required`, `consent_required` | A page was needed and the request said `prompt=none` |
| `unmet_authentication_requirements` | An essential `acr` that cannot be met (OIDC Core §5.5.1.1) |
| `access_denied` | The person refused on the consent page |

A request whose person signs in through an upstream identity provider has more answers, all sent back the
same way ([signing in through an organisation](../saml/federated-sign-in.md)): `access_denied` when that
provider authenticated nobody, with no consent page shown, or `login_required` when it declined to ask the
person under `prompt=none`; and `login_required`, or `account_selection_required` for
`prompt=select_account`, when it did not authenticate the person again as the request asked, whatever its
`prompt`.

## A request posted from another site

A browser does not send a session cookie set `SameSite=Lax` with a `POST` that another site makes it send
(RFC 6265bis), so a request a client posts to `/authorize` arrives without the session the browser holds.
Answered as it came, it would ask a signed-in person to sign in again, and the cookie of the new session
would replace the one they held.

So a `POST` of a form to `/authorize` that the browser says came from another site (`Sec-Fetch-Site:
cross-site`), that carries no session cookie, and whose every field a browser posts back unchanged, is
answered with a page of the provider's own origin that posts the same form again, pair by pair and in its
order. The second post is made from the provider's origin, carries the cookie and is not posted again; it is
read, judged and refused exactly as the first would have been. Nothing is decided on that page, and nothing of
the request is spent by the first post, a pushed reference included. The page submits itself where scripts
run, and where they do not it says "Your browser came from another site without your session. Use the button
below to continue.", in the language the `ui_locales` of the posted form asks for, or else the browser. A
browser that sends no `Sec-Fetch-Site` is answered as it always was, and a request in the query is never
touched.

Beside it, no answer of a page of the interaction plane to such a request, a `POST` or any method but `GET`
and `HEAD` from another site without the session cookie, carries a new session cookie: the one the session
listener would have written is taken off the response.

[:beffroi-arrow-right: Interactions](interactions.md), [response modes](response-modes.md) and [pushed
authorization requests](pushed-authorization-requests.md)
