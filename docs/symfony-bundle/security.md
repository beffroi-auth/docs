---
title: Security
status: draft
description: The firewalls, the authenticators, and what a session holds.
---

# Security

The bundle brings its own authenticators for the interaction plane and expects nothing of the host
application's security configuration beyond a firewall to put them on. The provider's session is its own: it
records what was proven, and it is not the host application's login session.

The standalone application declares two firewalls: the protocol endpoints, which authenticate their clients
themselves and open no session, and the interaction pages, where the logins of the provider live.

``` yaml title="config/packages/security.yaml"
security:
    providers:
        beffroi:
            id: Beffroi\Bundle\Security\IdentityUserProvider
    firewalls:
        beffroi_protocol:
            pattern: ^/(\.well-known/(openid-configuration|oauth-authorization-server)|jwks|token|userinfo|introspect|revoke|par|device_authorization|backchannel_authentication|register(/.+)?)$
            security: false
        beffroi_interaction:
            lazy: true
            provider: beffroi
            user_checker: Beffroi\Bundle\Security\UserChecker
            entry_point: Beffroi\Bundle\Security\PasswordLoginAuthenticator
            custom_authenticators:
                - Beffroi\Bundle\Security\PasswordLoginAuthenticator
                - Beffroi\Bundle\Security\PasskeyLoginAuthenticator
                - Beffroi\Bundle\Security\TotpLoginAuthenticator
                - Beffroi\Bundle\Security\UpstreamAssertionAuthenticator
```

Each authenticator is one way in: a password, a passkey, the code of a second factor, and the assertion an
[upstream SAML identity provider](../saml/federated-sign-in.md) posts to the assertion consumer service. Every
one of them ends in the same place, the core opening or refreshing the session under the floor of the
tenant, so the order of a login is written once whichever door it came through.

**A post from another site never sets a session cookie.** Under `SameSite=Lax` a browser keeps the session
cookie back from a `POST` that comes from another site. A page of the interaction plane answering such a post
with the cookie of a new session would replace the one the browser holds and sign it out of the provider, so
that cookie is taken off the answer. The four endpoints another site posts a browser to on purpose, the
authorization endpoint, the end session endpoint and the SAML single sign-on and single logout services, post
the request again from the provider's own origin instead, and the second post carries the session.

This page will describe the authenticators in full, and the rate limits that apply.
