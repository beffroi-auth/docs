---
title: Device code
description: Signing a person in on a device with no browser or no keyboard, RFC 8628, the two endpoints, the page where the code is confirmed, and the polling rules.
---

# Device code

The device authorization grant (RFC 8628) signs a person in on something that has no browser or no
keyboard to sign them in with. The device asks the provider for two codes, shows one of them to the person,
and polls the token endpoint with the other while the person confirms the code in a browser somewhere else.

``` mermaid
sequenceDiagram
    autonumber
    participant D as Device
    participant P as Beffroi
    participant B as Browser of the person
    D->>P: POST /device_authorization
    P->>D: device_code, user_code, verification_uri
    D-->>B: The user code and where to type it
    B->>P: GET /device, sign in, type the code
    B->>P: Allow
    loop Every interval
        D->>P: POST /token with the device_code
        P->>D: authorization_pending, then the tokens
    end
```

## Registering a device

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        living-room-tv:
            client_name: 'Living room TV'
            token_endpoint_auth_method: none
            grant_types: ['urn:ietf:params:oauth:grant-type:device_code', refresh_token]
            scope: 'openid profile offline_access'
```

A device that cannot keep a secret is a public client, `token_endpoint_auth_method: none`; a confidential
client is served the same way. It registers no redirect URI: nothing of this flow sends a browser back to the
client, so a redirect URI is refused unless the client is also registered for `authorization_code`. A public
client gets a refresh token only by asking for `offline_access` ([refresh token](refresh-token.md)).

## Starting: the device authorization endpoint

`POST /device_authorization` (RFC 8628 §3.1) authenticates the client exactly as the token endpoint does,
then reads what it asks for. Its errors are the JSON of RFC 6749 §5.2, never a redirection and never a page.

| Parameter | |
|---|---|
| `scope` | Required, among the scopes the client registered. RFC 8628 §3.1 makes it optional; here it is what the person is shown, and a request naming nothing would ask them to agree to everything the client ever registered |
| `resource` | Optional and repeatable, among the resources the client registered (RFC 8707 §2) |

| Refusal | Error |
|---|---|
| The client is not registered for the device code grant | `unauthorized_client` |
| No `scope` | `invalid_request` |
| A scope the client did not register, or a `scope` that is not a list of scope tokens | `invalid_scope` |
| A resource the client did not register, or one that is not an absolute URI without a fragment | `invalid_target` |

The answer is `200`, never cached (`Cache-Control: no-cache, no-store`, RFC 8628 §3.2):

``` json
{
    "device_code": "GmRhmhcxhwAzkoEqiMEg_DnyEysNkuNhszIySk9eS0k",
    "user_code": "WDJB-MJHT",
    "verification_uri": "https://op.example.com/device",
    "verification_uri_complete": "https://op.example.com/device?user_code=WDJB-MJHT",
    "expires_in": 600,
    "interval": 5
}
```

**The device code** is 256 random bits in base64url, 43 characters, which only the device holds.

**The user code** is eight characters out of twenty consonants, `BCDFGHJKLMNPQRSTVWXZ`, shown in two groups
of four. With no vowel it spells no word, and no character of it is read for another (RFC 8628 §6.1). Eight
characters out of twenty are a little over 34 bits, which is worth something only because guessing it is
slow (§5.1): the page below counts the codes that are refused. No two requests alive at once hold the same
user code.

The provider keeps the SHA-256 of both codes, never the codes, beside the client, the scopes, the resources
and where the device asked from.

| Option | Default | At most | What it is |
|---|---|---|---|
| `tokens.device_code_ttl` | `600` seconds | `1800` | How long both codes live |
| `tokens.device_code_interval` | `5` seconds | `30` | How long the device waits between two polls |

## Confirming: the page at `/device`

`verification_uri` is `/device` under the issuer, a page of the interaction plane
(`beffroi_interaction_device`), and `verification_uri_complete` is the same page with the code already in
it, for a device that can show a link or a QR code.

1. **The person signs in first**, at the login of the provider, and comes back to the page with the code it
   carried. No code is read before somebody is signed in.
2. **They type the code**, in upper or lower case, with or without the dash, with or without spaces.
3. **The page shows what they are about to allow**: the name of the provider, the account they are signed in
   as, the name of the client and the code, where the request came from, by its address and what its user
   agent says, every scope of the request, and a warning that whoever did not start this on a device of their
   own refuses it.
4. **They allow or refuse**, with a `POST` that carries the form token of the page. Nothing is approved on a
   `GET`, so a link followed from a screen, or fetched ahead of time by a browser, approves nothing.

Allowing records a consent to those scopes for that client, as the consent page of a browser flow does, and
freezes on the request the session and what that session had proven. Refusing ends the request: the device
learns `access_denied` at its next poll, and nobody is asked twice about the same code.

A code that names no request waiting for an answer, because it was never issued, expired, was answered
already or belongs to another tenant, gets one refusal whatever the reason, answered `400`. Only those
refusals are counted, against the person signed in: after five of them in a sliding minute, the page answers
`429` to every code until the window has room again. The count is the one the codes of a second factor are
counted on.

## Polling: the token endpoint

The device polls `POST /token` with `grant_type=urn:ietf:params:oauth:grant-type:device_code` and its
`device_code` (RFC 8628 §3.4), authenticated as it was at the device authorization endpoint. The answers
come in the order the device can act on them (RFC 8628 §3.5):

| Answer | When |
|---|---|
| `invalid_grant` | The device code is unknown, or was issued to another client |
| `expired_token` | The request is past its lifetime: the device starts a new one |
| `access_denied` | The person refused |
| `slow_down` | Nobody has answered yet, and the device polled sooner than its interval allows: the interval grows by five seconds, for this request and for every poll after it |
| `authorization_pending` | Nobody has answered yet |
| `invalid_grant` | The person allowed, and the code was spent already, or the session they allowed with has ended or is past its expiry |
| The tokens | The person allowed |

Every poll is recorded, the refused ones included, so asking again buys no faster answer; a request that has
an answer is answered however soon it is asked. The device code is spent once, atomically, by the first
poll after the approval: of several polls at once, exactly one is served.

The tokens are those of an ordinary authorization, descending from the session the person approved with: an
access token addressed to the resources the device named at the device authorization endpoint, or to the
client itself when it named none; an ID token when `openid` was among the scopes, without a `nonce`; and a
refresh token when one is due, starting a family with the absolute lifetime of every other. They are bound
to what the polling request binds them to ([grants](index.md#what-the-token-endpoint-does)), never to anything
the browser that approved proved.
