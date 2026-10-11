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

This page will describe each page, the blocks to override, and what must not be removed from them.
