---
title: Logout
status: draft
description: Ending a session, and telling the others.
---

# Logout

Three specifications, and they are not interchangeable: RP-initiated logout is a client asking for a session
to end, front-channel logout tells the other clients through the browser, and back-channel logout tells them
server to server with a signed logout token. A provider that implements only the first one has not logged
anybody out of anywhere else.

**A session is shared with SAML.** The session a client signed in under is the one the SAML service providers
of the browser signed in under too. When it ends at the end session endpoint, the front-channel logout page
comes first, and the browser then goes on to tell each SAML service provider of the session before it reaches
the `post_logout_redirect_uri`: [single logout](../saml/single-logout.md) says how that chain is played.

**Every end of a session revokes what was issued under it.** At the end session endpoint, from the page of the
account, by the console, by a SAML logout request or replaced by a new login: the refresh tokens issued in the
session are revoked and its opaque access tokens removed, beside the back-channel logout tokens sent to its
clients.

This page will describe each one, what a client registers for it, and what a logout can and cannot promise.
