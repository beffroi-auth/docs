---
title: Routes and planes
description: Importing the routes under the issuer, the two planes their names carry, and restricting a process to one of them.
---

# Routes and planes

Every route of the bundle is declared on its controller, one action per class, and its name carries its
plane: `beffroi_protocol_*` for what a client or a resource server calls, `beffroi_interaction_*` for what a
browser reads. `BEFFROI_PLANE` restricts a process to one of them, so that a provider can serve the protocol
on machines a browser never reaches, from the same build.

## Importing the routes

``` yaml title="config/routes/beffroi.yaml"
beffroi:
    resource: '@BeffroiBundle/config/routes.php'
```

**The routes are imported under the path of the issuer.** A provider whose issuer is
`https://op.example.com` imports them with no prefix, and one whose issuer is `https://example.com/idp`
imports them under `prefix: /idp`. Every endpoint the provider announces is located under the origin of the
issuer and the path the router gives it, never under the `Host` of the request. A prefix that disagrees with
the path of the issuer is refused at the first request that needs the endpoints, the discovery document among
them. Routes imported at the root for the issuer `https://example.com/idp` give:

``` text
The discovery document is served at "https://example.com/.well-known/openid-configuration" but the issuer "https://example.com/idp" makes clients look for it at "https://example.com/idp/.well-known/openid-configuration" (OIDC Discovery section 4.1): mount the routes of the bundle under the path of the issuer.
```

The metadata of both SAML roles are held to the same rule, and refused the same way.

**The root of the application is not the bundle's.** No route of the bundle is `/`. The standalone
application, whose issuer is an origin, sends `/` to the home of the account, with a route of its own whose
name carries the interaction plane, so a process that serves the protocol alone answers it `404` like every
page meant for a browser.

!!! warning "Import the routes by name, never through `routing.controllers`"

    The `routing.controllers` resource Symfony 8.2 offers routes every service that carries a `#[Route]`
    attribute, whatever file imports it and with no prefix. It would put the routes of the bundle at the root
    of an issuer that has a path, and the endpoints of the conformance tools below in every environment. The
    standalone application imports its own controllers one file at a time, for the same reason.

### Two files for development only

The bundle ships two more files of routes, which its own `routes.php` does not import: the endpoints the
FIDO Conformance Tools drive, and the endpoint the OpenID conformance suite answers a backchannel request
with when nobody is there to answer it. They are not an API of the product. An application imports them in
development, under a prefix of its own:

``` yaml title="config/routes/conformance.yaml"
when@dev:
    beffroi_fido_conformance:
        resource: '@BeffroiBundle/config/routes/fido-conformance.php'
        prefix: /fido/conformance
    beffroi_ciba_conformance:
        resource: '@BeffroiBundle/config/routes/ciba-conformance.php'
        prefix: /ciba/conformance
```

Their names, `beffroi_fido_conformance_*` and `beffroi_ciba_conformance_approval`, carry no plane.

## The two planes

| Plane | Route names | Who calls it | What is on it |
|---|---|---|---|
| Protocol | `beffroi_protocol_*` | A client or a resource server, server to server | The discovery document and the RFC 8414 metadata, the JWK Set, the token, UserInfo, introspection, revocation, pushed authorization, device authorization, backchannel authentication and registration endpoints, and the metadata of both SAML roles |
| Interaction | `beffroi_interaction_*` | A browser, with a person in front of it | The pages and the redirections a browser follows, and what those pages fetch: the authorization endpoint, the login, the consent, the logout, the device page, third party initiated login, the enrolment of a first passkey, the choice of a language, the pages of the account and the archive they hand over as a file, the options of a passkey ceremony in JSON, the scripts the pages load, and the SAML services a browser carries messages to |

[:beffroi-arrow-right: Every route, with its method and path](../reference/endpoints.md)

What tells the planes apart is the name and nothing else. A route is of the protocol plane because its name
starts `beffroi_protocol_`, so a route the bundle gains is in its plane by being routed, and a route of the
host application, whose name starts with neither, belongs to no plane.

## Restricting a process to one plane

| `BEFFROI_PLANE` | What the process serves |
|---|---|
| `all` | Both planes. The default when the variable is not set |
| `interaction` | The routes of the interaction plane, and the routes of no plane |
| `protocol` | The routes of the protocol plane, and the routes of no plane |

The variable is read by the process and not compiled into the container, so one build serves the three.
Every process imports the same routes and declares the same firewalls; what differs between the process that
serves the browsers and the one that serves the clients is that one line of its environment.

``` dotenv title=".env.local"
BEFFROI_PLANE=protocol
```

**A route of the other plane answers `404`**, the answer an unknown path gets, and the exception says why:

``` text
The route "beffroi_interaction_login" belongs to a plane this process does not serve (BEFFROI_PLANE=protocol).
```

The refusal is made once the router has named the route and before the firewall reads anything, so a
request refused for its plane opens no session and is not counted against the load budget of its origin. A
route of the host application, and an endpoint of the conformance tools, is never refused.

**A value that is none of the three refuses every request of the process**, the routes of the host
application included. A plane nobody spelled right is not `all`.

## What every route of the two planes carries

Being of a plane is also what decides what the provider puts around a route.

- **The budget of its origin.** Every request to a route of either plane is counted against the address it
  comes from, before the firewall, and refused with `429` once the budget is spent.
  [Attempts and budgets](security.md#attempts-and-budgets) says how much and in which shape.
- **The headers of a page.** Every page the bundle renders on the interaction plane carries
  `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'`, `Referrer-Policy: no-referrer`
  and a `Cache-Control` that says `no-store`. The policy is a floor a deployment replaces with its own, and
  [the pages](pages.md#the-headers-of-a-page) say what a page adds to it.
- **The rule of a post from another site**, which is read on the interaction plane alone.
  [Security](security.md#a-post-from-another-site) says which posts it reaches.

The bundle writes no CORS header on any route. Which origins may read the answer of an endpoint is the
deployment's to declare.

## A second origin for the clients that present a certificate

A deployment whose TLS listener asks for a client certificate on a host of its own names that host, and the
endpoints are located a second time under it, with the same paths (RFC 8705 §5):

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    mutual_tls:
        origin: 'https://mtls.op.example.com'
```

The discovery document announces them in `mtls_endpoint_aliases`. The issuer does not change: an alias is
another way to the same provider, not another provider. With no origin named, the document announces no
alias, and a client that authenticates by mutual TLS reaches the ordinary endpoints.

[:beffroi-arrow-right: Mutual TLS](../oidc/sender-constrained/mutual-tls.md)
