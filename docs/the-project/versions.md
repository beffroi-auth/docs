---
title: Versions
description: How the packages are versioned, and how this documentation follows them.
---

# Versions

## The packages

The eight packages share one version number, released together from the monorepo. A minor version has its
own maintenance branch, named after it: `0.1`, `0.2`, then `1.0`, `1.1`, and so on. A fix goes to the
oldest branch it applies to and is merged forward; a feature goes to the newest.

Until `1.0` the public API may change between minor versions, and what changes is written in the
[migration guide](../migration/index.md) of the version that changes it.

## This documentation

One branch of [`beffroi-auth/docs`](https://github.com/beffroi-auth/docs) per version of the packages, with
the same name. The selector at the top of the page switches between them, and `latest` points at the
newest released version, which is what the root of the site serves.

So a page you read always belongs to a version: it describes what that version does, not what the next one
will. A page that is not written yet carries a pencil in the navigation rather than a sentence that sounds
true.

## Supported versions

| Version | Documentation | State |
|---|---|---|
| 0.1 | this site | in development, nothing released |

The support window of a released version is not fixed yet. It will be written here, as a rule rather than
a promise per version, before `0.1` is published.
