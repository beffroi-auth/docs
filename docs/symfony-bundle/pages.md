---
title: Pages
status: draft
description: Login, consent, logout, device, and making them yours.
---

# Pages

The bundle ships the pages a person sees, styled with Tailwind, translated, and overridable like any Twig
template of any bundle. They are deliberately plain: a provider's pages are the deployment's own, not the
project's advertisement.

**What a tenant shows of itself is on every page**: its name, the logo it names, and the two colours it
names, the one the buttons and the links are drawn in and the colour of what is written on them. They are
read from the tenant at every render rather than hard-coded in a template, so a deployment that declares
none of them is served the pages it has always been served. The logo is loaded by the browser of the
visitor and never by the provider, and the pages name its origin in their content policy.

**The login page offers what the tenant admits.** It shows the logins the firewall wires that the [floor of the
tenant](../core/tenants.md#the-floor-of-its-logins) accepts: a tenant that signs its people in by passkey
shows no password field and no username, the passkey naming its own user. A tenant that federates domains to
[upstream identity providers](../saml/federated-sign-in.md#the-login-page-asks-for-the-address-first) asks for
the address first, one field and nothing else, and sends an address of those domains to its provider.

**Three pages post a form for the browser.** One answers a client that asked for `response_mode=form_post`
(OAuth 2.0 Form Post Response Mode); one carries a SAML message to a peer, a response or a logout message to
a service provider, a request to an upstream identity provider; the third posts again, from the provider's own
origin, a form another site posted without the session cookie. Each submits itself with the one script its
content policy allows by its hash, and keeps a button for a browser that runs no script. Their words are
translated like every other page's.

This page will describe each page, the blocks to override, and what must not be removed from them.
