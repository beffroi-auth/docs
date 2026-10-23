---
title: Contributing
description: How to report a problem, send a patch, and build this documentation locally.
---

# Contributing

## Reporting something

| What | Where |
|---|---|
| A bug, a question about the protocol, a missing feature | [beffroi-auth/beffroi](https://github.com/beffroi-auth/beffroi/issues) |
| A page of this site that is wrong, unclear or missing | [beffroi-auth/docs](https://github.com/beffroi-auth/docs/issues) |
| A vulnerability | Privately, through the security advisories of the code repository. Never in a public issue |

## Sending a patch to the code

One issue, one branch, one pull request. The branch is named `type/<issue>-<slug>`, for instance
`feat/162-dpop`, and the commit message says what the change does: `type(scope): what it does, lowercase,
no final period (issue #N)`.

Target the branch of the version your change belongs to: a fix goes to the oldest branch it applies to, a
feature to the newest. The quality gate runs on every pull request: the test suite, static analysis at the
maximum level, the architecture rules, the formatter, and mutation testing on the lines you changed.

Tests have a fixed shape in this project. One test verifies one behaviour, laid out in `// Given`,
`// When` and `// Then` blocks, and its name cites the section of the specification it verifies.

## Editing a page of this site

Every page has a pencil at the top right that opens it in GitHub, on the branch of the version you are
reading. For more than a typo, clone the repository and run the site locally:

``` bash
git clone git@github.com:beffroi-auth/docs.git
cd docs
make install
make serve
```

The site is then on `http://127.0.0.1:8000`, rebuilt as you save. Before opening the pull request:

``` bash
make check
```

That is the same build continuous integration runs: a strict build, where a broken internal link, a
missing anchor or a page absent from the navigation is an error.

### The rules a page follows

- A page states the present state. It never tells how it got there, and it carries no changelog of its own.
- One page, one subject, named in its title. The navigation is the table of contents.
- A page that is not written yet carries `status: draft` in its front matter, and the navigation shows a
  pencil. Better an honest stub than a page that sounds finished.
- Specifications are cited by number and section, for instance RFC 9449 §4.3 or OIDC Core §3.1.3.7.
- English, full sentences, no dashes used as punctuation.
- A figure, a limit or a default that appears on a page must be the one the code applies.
