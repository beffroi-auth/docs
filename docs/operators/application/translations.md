---
title: Translations
description: Every string translated, the two lists of languages, and how a page decides which one it speaks.
---

# Translations

Every user-facing string goes through the translator, in XLIFF with `intl-icu` for plurals and parameters,
in the `beffroi` domain. The application holds one catalogue per language it ships, thirty-one of them. They
are the official languages of the European Union but Irish and Maltese, English being official in Ireland and
Malta: Bulgarian (`bg`), Croatian (`hr`), Czech (`cs`), Danish (`da`), Dutch (`nl`), English (`en`), Estonian
(`et`), Finnish (`fi`), French (`fr`), German (`de`), Greek (`el`), Hungarian (`hu`), Italian (`it`), Latvian
(`lv`), Lithuanian (`lt`), Polish (`pl`), Portuguese (`pt`), Romanian (`ro`), Slovak (`sk`), Slovenian (`sl`),
Spanish (`es`) and Swedish (`sv`). Then Albanian (`sq`), Bosnian (`bs`), Catalan (`ca`), Icelandic (`is`),
Macedonian (`mk`), Norwegian Bokmål (`nb`), Serbian (`sr`), Turkish (`tr`) and Ukrainian (`uk`):

```
translations/beffroi+intl-icu.en.xlf
translations/beffroi+intl-icu.fr.xlf
translations/beffroi+intl-icu.de.xlf
...
```

The catalogues are code of the application, like its templates: adding a language is one more catalogue of
the same domain, holding every key of the English one and nothing else, its name in itself under
`language.<code>` in every catalogue, which is how the language control names it, and
`framework.enabled_locales` naming it in `config/packages/translation.yaml`.

The English of the catalogue is British and its Portuguese that of Portugal, and a date is written as
`en_GB` and `pt_PT` write one: "23 Nov 2026, 14:05 UTC" in English. Serbian is written in Cyrillic. The font of
the pages draws every one of these languages, Greek and Cyrillic included.

A deployment serves every language the application ships, or those `BEFFROI_LOCALES` names, as a JSON list
(`'["fr","en"]'`). `DEFAULT_LOCALE` is the one a page falls back to, and it is one of them: a list that leaves
it out is refused, and so is a language the application has no catalogue for. The discovery document
announces the languages served in `ui_locales_supported` (OIDC Discovery 1.0 §3), the default first, as language
tags (RFC 5646).

!!! info "The `error_description` of the protocol is not translated"

    It is addressed to the developer of the client, in ASCII, as RFC 6749 §4.1.2.1 asks. What a person
    reads on the error page is the translated sentence of the error code, and the description sits under
    it, in the language of the specification.

## Two lists of languages, two questions

| List | What it answers | Where it comes from |
|---|---|---|
| The languages this deployment serves | What a page can be written in | `BEFFROI_LOCALES`, or every language the application ships when it names none, with `DEFAULT_LOCALE` in front |
| The languages a person can say they read | What the `locale` claim of a person may name | Every locale ICU has data for, each under its own name in itself |

They are two lists because they answer two questions: `locale` is a claim of OIDC Core §5.1 and not a
setting of this provider, so a provider whose pages speak two languages still holds the claim of somebody
who reads a third. What that claim names is read against the first list wherever it is the language of a
page or of a message.

A tag is matched as Symfony matches an `Accept-Language`: `fr-CA` gives `fr_CA` when that locale is
served and `fr` otherwise, a script subtag is kept, and a tag no served locale matches is ignored rather
than refused.

## Which language a page speaks

**A signed-in person reads the pages in the language of their record**, and changes it where that record
is changed. That is the first answer tried, before anything the browser asked for. A record that names
nothing, or names a language this deployment does not serve, leaves the rest of the chain untouched.

For a visitor who is not known yet, the language of an interaction is chosen once, on arrival at
`/authorize`, and kept on the interaction so the next page of the same journey reads in it:

1. the language this browser asked for;
2. `ui_locales` of the request, read against the served languages;
3. `Accept-Language`, read the same way;
4. the default locale of the deployment.

What the visitor asked for comes before `ui_locales` because `ui_locales` is an end-user preference the
client passes on (OIDC Core §3.1.2.1), which is a second hand, and somebody who has just named their
language on the page is the first. Pages with no interaction behind them, an error before the first step
of an authorization, an unknown page, the logout confirmation and the page after it, speak the language of
the browser; the logout reads the `ui_locales` of its own request first, as RP-Initiated Logout §2 allows.

The language is never in the URL. The relying party does not know it, and a login URL that changes with
the language is a second address for every page.

## How a person chooses one

A form and no script: `POST /locale`, one button per language the deployment serves, rendered beside the
choice of a theme on every page that extends the layout. Below two languages there is nothing to offer and the
control is not rendered at all, and a page whose language was decided by the record of a signed-in person
says so, so the control offers nothing there either.

What is asked for is read against the served languages, and a tag nobody serves changes nothing. The
choice is then written in three places, because they answer three questions:

| Where | What it answers |
|---|---|
| The `locale` slot of the preferences of this browser | The language the next journey from this browser starts in |
| The interaction in progress | The language its next page is read in |
| The `locale` claim of the account, when somebody is signed in | The language this provider writes to that person in, outside any request of theirs |

The claim is written on a lane, nothing in the request waiting on the result, and it replaces that claim
and nothing else: describing a whole profile is what provisioning does, and it clears what it is not told.

**The preferences of a browser travel on one cookie**, `__Host-beffroi_preferences`, with a slot per
preference: the language this visitor asked for, the theme they read the pages in, and whatever a
preference wired beside them declares. It is read by no script, never leaves the requests of that browser,
goes out over TLS only and is worth a year, so somebody who said it once is not asked again. It is not the
HTTP session, deliberately: the protocol plane opens no session, a language in one would open a session
for every visitor who never signed in, and signing out invalidates a session whole, which would lose a
choice made for a year.

## Dates

A date a person reads says which clock it is on, and neither of the two things that decide it belongs to
the provider.

- **The clock is the one that person holds.** `zoneinfo` is a claim of OIDC Core §5.1, so it is read as a
  zone rather than taken for one: it may be absent, and it may name a zone this process cannot resolve, in
  which case the clock of the deployment answers.
- **The words and the order are ICU's**, in the language the page is written in. A date is not a string to
  translate but a convention of a locale, so a deployment that serves a language gets the dates of that
  language without writing a catalogue entry for them.

The zone is always named, by its abbreviation when it has one and by its offset otherwise: an hour without
its zone is an hour a reader cannot check. The machine readable form stays in the `datetime` attribute of
the element that carries it, which gives the instant with its offset. The dates the console prints do not
go through any of this, an administrator reading them beside a server.

The application requires `ext-intl`, which its `+intl-icu` catalogues need as well.
