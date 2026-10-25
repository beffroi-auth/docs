# The documentation of Beffroi

The public documentation of [Beffroi](https://github.com/beffroi-auth/beffroi), an identity provider for the
Symfony ecosystem: the identity core, the OAuth 2.0 and OpenID Connect module, the Symfony bundle and the
standalone application.

Published with [MkDocs](https://www.mkdocs.org/) and
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) on GitHub Pages:
**<https://beffroi-auth.github.io/docs/>**

## Writing

```bash
make install   # the toolchain, in .venv, from requirements.txt
make serve     # http://127.0.0.1:8000, rebuilt as you save
make check     # the strict build continuous integration runs
```

`make check` is the gate: a broken internal link, an anchor that does not exist, a page absent from the
navigation or a navigation entry without a page fails the build.

Without Python at hand, a preview with no plugins is one command:

```bash
docker run --rm -p 8000:8000 -v "$PWD":/docs squidfunk/mkdocs-material
```

## Where things are

| Path | What it is |
|---|---|
| `mkdocs.yml` | The site: theme, extensions, plugins, and the whole navigation |
| `docs/` | The pages, one directory per section of the navigation |
| `docs/assets/stylesheets/beffroi.css` | The look, from the brand guidelines. The tokens at the top of the file carry the colours, the type, the rules and the cuts |
| `docs/assets/fonts/`, `docs/assets/images/` | The typefaces with their licences, the logo, the favicons and the share image, copied from the brand kit |
| `docs/overrides/` | Theme partials: the logo in the colourway of the ground, and the head of every page |
| `docs/overrides/.icons/beffroi/` | The icons of the brand the pages use, written `:beffroi-<name>:` |
| `requirements.txt` | The toolchain, pinned. Continuous integration installs exactly this |
| `.github/workflows/check.yml` | The strict build, on every pull request |
| `.github/workflows/pages.yml` | The publication: one version per branch, through mike |
| `.github/workflows/default-branch.yml` | A new version branch becomes the default branch |

## One branch per version

A branch of this repository is a version of the packages: `0.1`, `0.2`, then `1.0`, `1.1`, and so on. A
push to one of them publishes it under its own name, and the newest one also carries the `latest` alias,
which the root of the site redirects to. The selector at the top of the page switches between them.

So a fix that applies to several versions is merged forward, like a fix in the code, and a page never
describes a version other than the one it is in.

### Opening a new version

```bash
git switch -c 1.0 0.2          # from the version it continues
# in mkdocs.yml, point edit_uri at the new branch
git push -u origin 1.0         # publishes it, and moves "latest" and the default branch
```

## Contributing

Every page carries its own rules, and they are short: a page states the present state, never how it got
there; a page that is not written yet says so with `status: draft` rather than sounding finished; a
specification is cited by number and section. The whole list is on
[the contributing page](docs/the-project/contributing.md).

Issues about the documentation go here. Issues about the code go to
[beffroi-auth/beffroi](https://github.com/beffroi-auth/beffroi/issues).

## Licence

MIT, as the packages it documents.
