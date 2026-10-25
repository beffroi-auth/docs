---
title: Interactions
status: draft
description: What happens between the request and the answer.
---

# Interactions

An interaction is the part a person sees: signing in, proving a second factor, agreeing to what a client
asks. The request waits on it, identified rather than held in a session, so a person can finish it in
another tab and so a provider restricted to the protocol plane never serves it.

**On a tenant that federates domains**, the login of an interaction asks for the address first, and an address
of a domain an upstream identity provider answers for is sent to that provider; a `login_hint` that is such an
address sends the browser there without showing the page. What the client asked of the login, `prompt=login`,
a `max_age` or a step-up, is asked of the provider in turn and checked against the instant the person
authenticated there: [signing in through an organisation](../saml/federated-sign-in.md) says how.

This page will describe the model, `prompt`, `max_age`, `acr_values`, and what a client learns of an
interaction that did not finish.
