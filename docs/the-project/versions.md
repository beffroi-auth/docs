---
title: Versions
description: How the packages and the image of the application are versioned, and how this documentation follows them.
---

# Versions

## The packages

The packages share one version number, released together from the monorepo. A minor version has its own
maintenance branch there, named after it with `.x`, a name that matches `^\d+\.\d+\.x$`: `0.1.0` is released
from `0.1.x`, and the next minor is written on `0.2.x`. Each package is mirrored, read only, into a repository
of its own, which carries those branches and the tags of the releases and nothing else. A fix goes to the
oldest branch it applies to and is merged forward; a feature goes to the newest.

Until `1.0`, which ships with Symfony 8.4, the public API may change between minor versions, and what changes
is written in the [migration guide](../migration/index.md) of the version that changes it.

## The image

The application is published as `ghcr.io/beffroi-auth/beffroi`, for `linux/amd64` and `linux/arm64`, under these
tags:

| Tag | What it names |
|---|---|
| `A.B.C` | The image of the release `A.B.C`, built when it is published |
| `A.B` | The highest release of `A.B` |
| `A` | The highest release of `A`, from `1.0.0` on |
| `latest` | The highest release of all |
| `A.B.x` | The last build of the maintenance branch, which follows the branch |
| `A.B.x-<commit>` | The build of one commit of the branch, named by the first seven characters of its hash |

A maintenance branch is built at every push that touches the packages or the application. The image names
each of its two base images, FrankenPHP's and Debian's, by its version, pinned by the digest of that tag, so
two builds of one commit start from the same PHP, FrankenPHP and Debian. Every day, Dependabot proposes on
`0.1.x` the version or the digest that follows, never another major version; once merged, it is in `0.1.x`,
and in `0.1` and `latest` with the next release.

## This documentation

One branch of [`beffroi-auth/docs`](https://github.com/beffroi-auth/docs) per version of the packages, named
`<major>.<minor>` with no `.x`: `0.1` documents the code of `0.1.x`, and `0.2` that of `0.2.x`. The selector at
the top of the page switches between them, and `latest` points at the newest released version, which is what
the root of the site serves.

So a page you read always belongs to a version: it describes what that version does, not what the next one
will. A page that is not written yet carries a pencil in the navigation rather than a sentence that sounds
true.

## Supported versions

| Version | Documentation | State |
|---|---|---|
| 0.1 | [doc.beffroi.tech/0.1](https://doc.beffroi.tech/0.1/) | released as `0.1.0`, supported |

Until `1.0`, only the latest release is supported: a fix ships in the next release, and an earlier `0.x`
release is not patched.
