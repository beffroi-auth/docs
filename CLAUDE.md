# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The public documentation of Beffroi, an identity provider for the Symfony ecosystem. It documents four
packages: `beffroi/core` (identity), `beffroi/oidc` (OAuth 2.0 and OpenID Connect), `beffroi/symfony-bundle`
(the Symfony integration) and `beffroi/op` (the standalone application). SCIM and SAML 2.0 have a section
each, and both say they are not implemented.

The code lives in `beffroi-auth/beffroi`, cloned at `~/Projects/idp/code`. Its design, its decisions and its
spikes live in `beffroi-auth/design`, cloned at `~/Projects/idp`. **Neither of those is this repository, and
neither is the audience of this one**: `design` is internal and in French, this site is public and in
English.

A static site built with MkDocs and Material for MkDocs, published on GitHub Pages, one version per branch
through mike. `README.md` has the commands.

## Non-negotiables

- **A page states the present state, as if it had always been so.** It never tells how it got there: no
  "was renamed", no "since version X this is", no amendment appended under a section. When something
  changes, the page is rewritten and the previous version lives in the git history.
- **A figure, a default, a limit, a route or an option on a page is the one the code applies.** Read it in
  `~/Projects/idp/code` before writing it here. Never infer an option name, a command signature or a claim
  from what would be reasonable.
- **What is not written yet says so.** `status: draft` in the front matter, and a stub that states the
  subject of the page and the specification it follows. Never a page that sounds finished and is not, and
  never a sentence invented to fill one.
- **The audience is whoever installs Beffroi**, not the team that writes it. No spike number, no decision
  number, no issue number, no internal date, no name of a person on any page.
- **Specifications are cited by number and section**: `RFC 9449 §4.3`, `OIDC Core §3.1.3.7`.
- **English, full sentences, no dash used as punctuation** (no em dash, no en dash). Same house style as
  the design repository, in the other language.

## The shape of a page

```markdown
---
title: The title in the navigation and in the browser tab
status: draft          # only while the page is a stub
description: One sentence, used by search engines and by the social card.
---

# The title again

...
```

- One page, one subject, named by its title. The navigation in `mkdocs.yml` is the table of contents, and a
  page absent from it fails the build.
- Internal links are relative paths to the `.md` file (`../core/keys.md`), never to the built URL.
- Hints are Material admonitions (`!!! info`, `!!! warning`), not GitBook `{% hint %}` blocks.
- Tabs for alternatives the reader chooses between (`=== "In a Symfony application"`), a table for facts.
- A code block carries its filename when the reader has to put it somewhere:
  ` ```yaml title="config/packages/beffroi.yaml" `.

## Adding a page

1. Write `docs/<section>/<page>.md` with the front matter above.
2. Add it to `nav:` in `mkdocs.yml`, in the place the reader would look for it.
3. `make check`. Strict mode fails on a broken link, a missing anchor, a page outside the navigation and a
   navigation entry without a page.

## The look

`docs/assets/stylesheets/beffroi.css` makes Material look like GitBook. Its first block is the tokens:
accent, foreground, background, border, radius, column widths, in both colour schemes. Change a colour
there and the whole site follows; do not add a hex value further down the file.

## Versions

A branch is a version of the packages: `0.1`, `0.2`, `1.0`, `1.x`. A push publishes it under its own name,
and the newest branch also carries `latest`, which the root redirects to. `edit_uri` in `mkdocs.yml` names
the branch, so it changes when a branch is created. A fix that applies to several versions is merged
forward.

## What not to do here

- Do not copy pages from `~/Projects/idp/docs`. That is the design repository: French, internal, and it
  answers a different question. A page here is written for whoever installs the thing.
- Do not document something the code does not do yet without saying it does not.
- Do not add a plugin or a theme feature without pinning it in `requirements.txt`.
