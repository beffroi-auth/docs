---
title: Mutual TLS
description: A client recognised by the certificate of its connection, the tokens bound to that certificate, the endpoint aliases, and how the certificate reaches PHP. RFC 8705.
---

# Mutual TLS

RFC 8705 has two halves, and the provider serves both. A client authenticates with the certificate it
presents at the TLS handshake (§2), and the tokens it receives are bound to that certificate (§3), so that a
token presented over a connection without it is refused wherever the binding is checked. The certificate is
the one the TLS listener of the deployment received, handed to PHP by that listener and never read from a
header of the request.

## Authenticating with a certificate

Two methods recognise a client by its certificate, and both are wired in the bundle. Either way the request
names the client in `client_id` and presents the certificate at the handshake: a request without a
certificate presents neither method.

| `token_endpoint_auth_method` | The certificate | What makes it the client's |
|---|---|---|
| `tls_client_auth` (RFC 8705 §2.1) | Issued by a certificate authority the TLS listener trusts | The one value the client registered, read out of the certificate and compared |
| `self_signed_tls_client_auth` (RFC 8705 §2.2) | Any, self-signed included | The client publishes it in its JWK Set, `jwks` or `jwks_uri`: the first certificate of the `x5c` of one of its keys (RFC 7517 §4.7), or the `x5t#S256` of one of them (§4.9) |

**A `tls_client_auth` client registers exactly one of the five values of RFC 8705 §2.1.2**, and a client
registered for any other method registers none of them: a declaration that does not hold is refused at boot,
and a registration that does not is refused.

| Member | Compared with the certificate |
|---|---|
| `tls_client_auth_subject_dn` | The subject distinguished name, in the string form of RFC 4514. The registered value is written again, when the registration is read, the way the provider writes the name it reads out of a certificate, so a name as `openssl x509 -noout -subject -nameopt RFC2253` prints it is registered as it is |
| `tls_client_auth_san_dns` | A `dNSName` entry of the subject alternative name, without regard to case (RFC 4343 §1). A wildcard entry is text like any other and is never expanded |
| `tls_client_auth_san_uri` | A `uniformResourceIdentifier` entry, as the text it is, with no normalisation |
| `tls_client_auth_san_ip` | An `iPAddress` entry, as the octets it stands for, so the registered text may be written in any form RFC 4291 §2.2 allows |
| `tls_client_auth_san_email` | An `rfc822Name` entry, as the text it is, nothing folded |

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        payments-app:
            token_endpoint_auth_method: tls_client_auth
            tls_client_auth_subject_dn: 'CN=payments-app,O=Example,C=FR'
            redirect_uris: ['https://payments.example.com/callback']
```

**The provider judges no chain.** Only the leaf certificate reaches PHP, so what makes a certificate
trustworthy, its chain, its validity period and its revocation, is judged by the TLS listener during the
handshake, against the authorities the deployment configures there. A self-signed certificate is trusted for
what the client published and for nothing else, as the keys of `private_key_jwt` are; a client that renews
its certificate publishes the new one before it presents it.

**A certificate beside another credential** does not make two methods. A client reaching the host that asks
for a certificate presents one because it was asked: the credential its request carries, a secret or an
assertion, authenticates it, and the certificate authenticates only a client registered for one of the two
methods above.

A request that names a client and does not prove it is refused with `invalid_client`, status `401`, and the
same description whatever the cause: a certificate that is not the registered one, a certificate the client
does not publish, a certificate that cannot be read, no certificate from a client registered for one. Each
refusal is an act of the journal, `client_authentication.failed`.

## Tokens bound to the certificate

Two clients get tokens bound to the certificate of their connection:

- a client that authenticated with `tls_client_auth` or `self_signed_tls_client_auth`, bound to the very
  certificate that authenticated it (RFC 8705 §3);
- a client that registered `tls_client_certificate_bound_access_tokens: true`, whatever way it authenticates
  (RFC 8705 §3.4). A token request of such a client that presents no certificate is refused with
  `invalid_request`, status `400`, before anything of what it came to spend is read.

Any other client that presents a certificate, because the listener asked for one, is not bound to it: binding
a client that never asked for it would break the resource servers it calls.

**What a bound token says.** An `at+jwt` carries `"cnf": {"x5t#S256": "<thumbprint>"}`, the base64url SHA-256
of the DER encoding of the certificate (RFC 8705 §3.1), and an opaque token keeps the same member in its
record. The token response says `"token_type": "Bearer"`: the client changes nothing in the way it presents
the token, the transport proving the holder at every request. The refresh token of a public client is bound
to the certificate as well; the one of a confidential client is bound to nothing, since the client
authenticates when it refreshes. A token request that proves the certificate and carries a [DPoP](dpop.md)
proof as well is refused with `invalid_dpop_proof`, a token being [bound to one thing](index.md#the-two-bindings).

**UserInfo honours a bound token only over a connection that presents the same certificate**, and refuses it
otherwise with `invalid_token`, status `401`, `WWW-Authenticate: Bearer error="invalid_token"`. A client
therefore reads UserInfo at the `userinfo_endpoint` of the aliases below: the ordinary host asks for no
certificate, and a request that reaches it proves none.

**Introspection describes a bound token whatever certificate the caller presented**, since the client it was
issued to may introspect it however it authenticates today, and its answer carries the `cnf` a resource server
needs to make its own check. A resource server of your own compares that thumbprint with the SHA-256 of the
certificate its own TLS connection received (RFC 8705 §3.2).

## The endpoint aliases

A deployment may serve the endpoints that read a certificate on a host of their own, whose listener asks for
one, and leave the ordinary host of the issuer asking for nothing, so that a browser is never asked for a
certificate at the authorization endpoint or on a page. The configuration names that host:

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    mutual_tls:
        origin: 'https://mtls.op.example.com'
```

| Option | Default | What it decides |
|---|---|---|
| `origin` | none | The scheme and the authority of the host whose listener asks for a certificate, without a path. The discovery document announces the aliases under it. Left out or empty, it announces none, and a client authenticating with a certificate reaches the ordinary endpoints, which is what a deployment serving one host does |

With an origin, the discovery document carries `mtls_endpoint_aliases` (RFC 8705 §5): the same paths, on the
other origin, for six endpoints.

``` json
{
    "mtls_endpoint_aliases": {
        "token_endpoint": "https://mtls.op.example.com/token",
        "userinfo_endpoint": "https://mtls.op.example.com/userinfo",
        "introspection_endpoint": "https://mtls.op.example.com/introspect",
        "revocation_endpoint": "https://mtls.op.example.com/revoke",
        "pushed_authorization_request_endpoint": "https://mtls.op.example.com/par",
        "device_authorization_endpoint": "https://mtls.op.example.com/device_authorization"
    }
}
```

The issuer does not change, and neither does anything else the document says: an alias is another way to
the same provider. The backchannel authentication endpoint reads a certificate as well, and is not among the
aliases. Independently of the origin, the document announces `tls_client_certificate_bound_access_tokens`
as `true` whenever a method that authenticates by certificate is wired, which the bundle does.

## How the certificate reaches the application

The bundle reads the certificate in one place, the server variable `SSL_CLIENT_CERT`, named after the one
mod_ssl sets: the leaf certificate in its PEM envelope, set by the TLS listener from the handshake it carried
out. An empty envelope, or no variable, is a request made without a certificate. A client controls every
header of its request and no variable of the process that serves it, so no header is ever read in its place.

**A certificate in a header is refused.** A request that carries `Ssl-Client-Cert`, `X-Ssl-Client-Cert`,
`X-Client-Cert` or `X-Forwarded-Client-Cert` is somebody trying, and is refused rather than served without
its certificate, so that a deployment placed behind a proxy that forwards one learns it on its first request.
The refusal is `invalid_request`, status `400`, at the seven endpoints that read a certificate: `/token`,
`/par`, `/introspect`, `/revoke`, `/userinfo`, `/device_authorization` and `/backchannel_authentication`. So
is a variable that does not hold a PEM certificate, the listener being misconfigured then.

=== "In the standalone application"

    The image carries a second site block, `/etc/frankenphp/mtls.Caddyfile`, for the host whose listener
    asks for a certificate. A deployment turns it on with three variables, and the host of `SERVER_NAME`
    keeps asking for nothing.

    | Variable | Read by | Value |
    |---|---|---|
    | `MTLS_SERVER_NAME` | Caddy | The name of the host that asks for a certificate |
    | `CADDY_EXTRA_CONFIG` | Caddy | `import mtls.Caddyfile`, which adds that site block |
    | `BEFFROI_MTLS_ORIGIN` | The application | The origin of that host, which becomes `mutual_tls.origin` |

    The image leaves `BEFFROI_MTLS_ORIGIN` empty and announces no alias until a deployment names the origin
    of its own host; the development stack names `https://mtls.op.localhost`.

    The site block asks for a certificate without requiring one (`client_auth` in `mode request`), so a
    client that authenticates another way completes its handshake on that host too. A certificate is only
    accepted with the signature of the handshake that proves its holder has the private key (RFC 8446
    §4.4.3), and the leaf is handed to PHP as `SSL_CLIENT_CERT`, empty when the client presented none.

    The block verifies no chain, so it accepts a certificate whatever authority issued it, which is what
    `self_signed_tls_client_auth` needs. A deployment that authenticates clients with `tls_client_auth` has
    that block verify a presented certificate against the authorities it accepts: that is where the chain
    is judged, and nowhere else.

=== "In a Symfony application"

    The web server that terminates TLS sets `SSL_CLIENT_CERT` to the PEM of the leaf certificate it
    verified, and leaves it empty when the client presented none. It asks for a certificate on the host the
    aliases point at, and judges there the chain of a certificate that `tls_client_auth` will rely on.

    A deployment whose edge hands the certificate over some other way implements
    `Beffroi\Bundle\Http\Tls\ClientCertificateResolverInterface`, which returns the certificate of a
    request or none, and aliases it in place of the resolver of the bundle, rather than teaching the bundle
    a header to trust.
