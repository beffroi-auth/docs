---
title: Users
description: 'A person of a tenant: the username, the subject clients know them by, the claims of their profile, and the source that created them.'
---

# Users

A user belongs to a tenant, is named by a username unique within it, and is known to clients by a subject
identifier that never changes, even when the username or the address does. The standard claims of OIDC Core
§5.1 are held beside the identity, each one a field of its own in the model rather than an entry in a bag of strings,
and the person names the source that created them. Their [credentials](credentials/index.md), their
[linked identities](linked-identities.md) and their [group memberships](groups.md) hang off the user.

## What a user holds

| Field | What it holds |
|---|---|
| Subject | The `sub` of OIDC Core §2: 1 to 255 printable ASCII characters, no space. Unique within the tenant, never changed and never given to anybody else |
| Username | What the person types to name themselves: 1 to 255 characters of [plain text](#plain-text) once the whitespace around it is trimmed, unique within the tenant and matched exactly, case included |
| Email address | Optional, a valid address, with a flag that says whether it was verified. An absent address cannot be verified. The mail that tells the person that [a backchannel request](../../developers/oidc/grants/backchannel-authentication.md#reaching-the-person) waits for them is written to it only while it is marked verified |
| Phone number | Optional, plain text of 64 characters at most, with a flag of its own that says whether it was verified. The text that tells them so is sent to it only while it is marked verified |
| Address | The structured claim of OIDC Core §5.1.1. An address with no member is no address, and is not held |
| Profile | The thirteen other claims of OIDC Core §5.1, below |
| Source | Local, or the upstream provider that created the person and the claims it holds of them |
| Dates | When the record was created, when it last changed, and when the account was disabled, if it was |

The subject stays readable in the database, a stable pseudonym that names a person without saying anything about
them; every other field of the person that says something about them is sealed under the data key of the tenant.
[Personal data](../../operators/tenant/personal-data.md) says how.

## The subject clients know them by

The subject is drawn when the user is created, a random UUID (version 4, RFC 9562 §5.4) that says nothing of
when the account was opened. An import brings its own instead, so that the clients of the provider it came
from find the same person under the same `sub`:

``` bash
bin/console beffroi:user:create alice --subject 248289761001
```

Nothing changes it afterwards: a new username or a new address leaves it as it was. It is the
`sub` a client receives, unless that client is registered for a pairwise identifier (OIDC Core §8.1), in which
case it receives one derived for its sector, and the [pairwise subjects](../../developers/oidc/pairwise-subjects.md) page
says how. The pages of the account show neither.

## Creating one

``` bash
bin/console beffroi:user:create alice --email alice@example.com
```

| Argument or option | What it says |
|---|---|
| `username` | What the user types to name themselves, unique in the tenant |
| `--email` | Their address, unverified |
| `--email-verified` | The address was verified by whoever provisions the user |
| `--subject` | The `sub` of an identity being imported, drawn otherwise |

A username or a subject the tenant already holds is refused, and so is an address or a subject that is not
well formed. The command prints the username, the subject, the email address with its state, the identifier of
the row and the slug of the tenant. It gives the user no credential: a password is
[`beffroi:user:set-password`](credentials/passwords.md), and a first passkey on a tenant that holds no password
is an [enrolment ticket](credentials/passkeys.md#a-first-passkey-from-a-ticket).

An administrator creates a person through the administration API as well, from their username and, when it is
known, their address and whether it was verified, under the same refusals. Creating a person is an act of
theirs, `person.created`, which names the administrator when one created them.

A person is also created by an upstream identity provider, [at their first sign-in through their
organisation](../../operators/saml/federated-sign-in.md#the-person). That person is named by their address, which is their
username, the address is verified, and the source says which provider created them.

## The claims of the profile

| Claim | What it holds |
|---|---|
| `name`, `given_name`, `family_name`, `middle_name`, `nickname`, `preferred_username` | Names |
| `profile`, `picture`, `website` | Three URLs, each absolute, `https` or `http`, with a host, and 2048 characters at most. A space or a control character anywhere in it is refused, and so is any other scheme, `javascript:` and `data:` among them |
| `gender` | A free string, OIDC Core §5.1 naming two values and allowing others |
| `birthdate` | `YYYY-MM-DD`, a day the calendar holds, or `YYYY` alone, `0000` standing for a year nobody knows |
| `zoneinfo` | The clock of the person, a name of the zoneinfo database |
| `locale` | The language the person reads |
| `email`, `email_verified` | The address and its flag |
| `phone_number`, `phone_number_verified` | The number and its flag |
| `address` | The six members of OIDC Core §5.1.1: `formatted`, `street_address`, `locality`, `region`, `postal_code`, `country` |

The names, `gender`, `zoneinfo` and `locale` are [plain text](#plain-text) of 255 characters at most. The
members of the address are plain text too: `formatted` and `street_address` hold 1024 characters at most, on
lines separated by line feeds, and the four others 255. A value that breaks a rule of the table or of this
paragraph is refused wherever it comes from.

**A claim that is not set is absent.** The provider holds nothing under that name, and a client is never sent
the claim with a null value: it is sent no claim at all. A flag goes with its value, so `email_verified` is
sent only beside an address and `phone_number_verified` only beside a number, and an address with no member is
no `address`. `updated_at`, the instant the record last changed, always has a value. Which claims a client
receives, by scope or by name, is [scopes and claims](../../developers/oidc/scopes-and-claims.md).

### Plain text

What somebody writes of a person, a group or a client is plain text: valid UTF-8, with no control character, no
line or paragraph separator, and no format character but the zero-width non-joiner and joiner that Persian and
the Indic scripts write words with, so that nothing in it breaks, reorders or hides a part of the line it is
shown on, and bounded in characters. The provider holds a value to it whatever path writes it, the pages of the
account, the administration API, an upstream provider, a registration or the console, and the refusal names the
rule: the administration API answers it with `400`, `invalid_request` and that sentence.

### Describing a user from the console

``` bash
bin/console beffroi:user:profile alice --given-name Alice --family-name Liddell --locale fr-FR
```

**It writes the whole profile.** What the command does not say is cleared, so a run says every claim the
person is to keep. A run that says nothing is refused rather than taken for a request to clear everything,
and a value left empty says nothing. The command prints the name, the given name, the family name, the phone
number and the postal address it wrote; reading a user without writing is `beffroi:user:show`.

| Claim | Option |
|---|---|
| `name`, `given_name`, `family_name`, `middle_name` | `--name`, `--given-name`, `--family-name`, `--middle-name` |
| `nickname`, `preferred_username` | `--nickname`, `--preferred-username` |
| `profile`, `picture`, `website` | `--profile-url`, `--picture`, `--website` (`--profile` is an option of the console itself) |
| `gender`, `birthdate`, `zoneinfo`, `locale` | `--gender`, `--birthdate`, `--zoneinfo`, `--locale` |
| `phone_number`, `phone_number_verified` | `--phone-number`, `--phone-number-verified` |
| `address` | `--address` for `formatted`, `--street-address`, `--locality`, `--region`, `--postal-code`, `--country` |

The email address is not among them. It is given when the user is created, and rewritten afterwards by the
upstream provider that [created the person](../../operators/saml/federated-sign-in.md#the-person), or by an administrator
through the administration API. No command renames a user.

### What an administrator says of a person

An administrator changes the username and the claims of a person through the administration API, with one JSON
merge patch (RFC 7396) of the document that reads the person: a claim set to `null` is taken away, and a new
address or number is unverified until the patch says it was verified. All of it is written or none of it. A
username another person of the tenant holds is refused, and so is a value that changes what the source of the
person holds. Each value that changed is a line of the history of the person, which names the administrator,
and the patch is one act, `person.described`, which carries the names of what changed and never a value. A patch
that changes nothing writes neither: it answers the person as they are, which is a read of them,
`administration.person_read`.

### What a person says of themselves

A person changes, on [the page of their account](../../operators/application/account.md#what-a-person-may-change-of-themselves),
the claims their tenant opens in `tenant.self_served_claims`, and no other: a tenant that opens none serves a
page that only reads. Fourteen claims can be opened: `name`, `given_name`, `family_name`, `middle_name`,
`nickname`, `preferred_username`, `birthdate`, `gender`, `locale`, `zoneinfo`, `profile`, `picture`, `website`
and `phone_number`, and a name none of them answers refuses the start. The rule is applied by the use case that
writes, for every caller, and not only by the page that shows the form.

- **A closed set is closed on the server.** Described by the person, `zoneinfo` takes a name of the zoneinfo
  database this PHP carries and `locale` one of the locales its ICU data holds, written as a BCP 47 tag, and
  anything else is refused; a PHP whose ICU holds no data closes no set for `locale`. `beffroi:user:profile`
  holds neither claim to these sets.
- **A new number is not a verified one.** A person who writes a telephone number takes back its verification,
  since what was proved was proved of the number that is gone.
- **What it said before is kept.** Each change writes what the claim said and what it says now, sealed, kept
  for `BEFFROI_HISTORY_RETENTION` days, 180 in the image, and read at `/account/profile/changes`. The act,
  `person.described_themselves`, goes to the journal of the person, which keeps the act and never the value.
  Saying again what a claim already says writes the act and no change.

Choosing a language on a page writes the `locale` claim of a signed-in person, and that claim alone.

## The source that created a person

**A person names the source that created them.** Local, for a person the console, a fixture or an import
created; or an upstream provider, for a person created at their [first sign-in through their
organisation](../../operators/saml/federated-sign-in.md#the-person), with the claims of their profile that provider fills.

**What a source holds, a manual description does not change.** `beffroi:user:profile` refuses a held claim said
otherwise, naming the provider, before anything is written; it keeps a held claim it is not told about rather
than clearing it, and it accepts one said with the value it already has, so a provisioning script can run
again. The page of the account offers the person no field for a held claim, and the use case behind it refuses
one posted by hand. A choice of language on a page leaves a held `locale` as the provider wrote it.

**What the provider stops saying is released.** At every sign-in through it, the source holds the address, the
telephone number when the provider said one, and those of the claims it fills that it said at that sign-in, and
nothing else: a claim it no longer says is left with the value it wrote last, and from then on the person, or
the console, may change it.

**The username follows the address.** A person a provider created is named by their address, and when the
provider sends another one, the username becomes that address in the same unit as the rest of the sign-in.

`beffroi:user:show` prints the source beside the identity: `local`, or the name of the provider followed by the
claims it holds. The source is sealed with the rest of the person, since the provider that created somebody
says which organisation they are of.

## Reading a user

``` bash
bin/console beffroi:user:show alice
```

It prints the username, the subject, whether the account is enabled, when it was created, the email address with
its state and the source, then the name, the given name, the family name, the phone number and the postal
address. Below them, one line per credential with its kind, identifier, name and dates, revoked ones
included, and for a passkey its authenticator: the model a source names, or `unknown` with its AAGUID, then
what the enrolment proved, `declared`, `verified` or `enterprise`, the serial number an enterprise attestation
carried, and `under a security alert` for a model the tenant admitted under one. Then one line per group with
the source of the membership and the date it was added. It writes nothing. The [console commands](../../operators/reference/console-commands.md) list what else reads a person:
`beffroi:user:sessions`, `beffroi:user:journal` and `beffroi:user:applications`.

## A disabled user

An account carries the date it was disabled, and a disabled person is refused at these places:

- every login, by password, by passkey or by code, after the credential was checked, so that the refusal
  costs what a wrong credential costs and says nothing of the state of the account;
- a sign-in through an upstream provider, before anything the provider said is written;
- a ticket of any kind, for a passkey, a password or an authenticator application, which is not issued for them
  and no longer opens anything once they are;
- an assertion of a trusted issuer at the token endpoint (RFC 7523 §3) that names them;
- an access token that names them, at UserInfo, at introspection, at the administration API, and presented to
  the token exchange (RFC 8693);
- a refresh token issued for them, at the token endpoint, refused with `invalid_grant`.

**Disabling a person ends every session of theirs.** The account is disabled first, so that no session opens
meanwhile, then each session ends as any other does: its clients are told through the back channel and its
refresh tokens are revoked. Enabling the person again gives nothing back, and they sign in anew.

``` bash
bin/console beffroi:user:disable alice
bin/console beffroi:user:enable alice
```

An administrator does the same through the administration API, and cannot disable the account they act with.
Each is an act of the person, `person.disabled` or `person.enabled`. A person already in that state is left as
they are, and no change is written; through the administration API, the answer delivers them as they are, which
is a read of them, `administration.person_read`. `beffroi:user:show` says `disabled since` and the date.
