---
title: Web push
description: Reaching a person through the push service of a browser they signed in with (RFC 8030), what a notification carries, and what becomes of it.
---

# Web push

A deployment that names a push subject reaches a person through the push service of a browser they signed in with
(RFC 8030): the person subscribes that browser on a page of their account, and the provider pushes to it when a
request waits for their answer and when a way of signing in to their account changes. It is one way a backchannel
authentication request (CIBA Core §7) reaches the person it names without a second application, beside mail and
SMS, and how a person learns, outside the request that made it, that a way into their account was added or taken
away (NIST SP 800-63B §4.1.2.1, §4.5). Nothing in a notification names the request or the credential it is about.

## Turning it on

Two variables of the environment fill `beffroi.web_push`:

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_WEB_PUSH_SUBJECT` | `mailto:operator@op.localhost` | The `subject`, the `sub` of the token the provider signs for a push service (RFC 8292 §2.1): a `mailto:` or `https:` URI at which a push service can reach the operator of the deployment. Naming one is what turns web push on, and an empty variable turns it off. The one of `.env` is the development stack's, so a deployment names its own |
| `BEFFROI_WEB_PUSH_TIMEOUT` | `3` | The `timeout`, the seconds one push to one push service is given, connection included, so that a push service that hangs does not hold a worker |

**Without a subject, web push serves nothing.** Its services and its routes are always wired, and the subject
is read when the container builds what web push changes: naming one or taking it away asks for a restart of the
processes and not for a new image. Without one, its two channels are not in the lane of notifications, no push
leaves the deployment, the tenant draws no application server key, and the page where a browser would subscribe
says that the provider does not tell browsers. A key drawn before the subject was taken away is read by nothing
until a subject is named again.

## The application server key

A browser subscribes under the public half of a key pair of the tenant, and its push service then takes only
pushes signed by that key (RFC 8292 §4.2). The pair is drawn like every key of the tenant, under the name
`VAPID`, ECDSA over P-256, and sealed by the [key management service](key-management.md):

``` bash
bin/console beffroi:keys:generate --algorithm=VAPID
```

It is a key the tenant hands out rather than publishes: it is in no JWK Set, and the page of notifications
hands its public half to the browser, as the uncompressed point of RFC 8292 §3.2 in base64url. A deployment
that turns web push on and draws no key has no key to hand out, and the page says so in the same words.

**A subscription is bound to the key it was made under**, by its `kid`. A rotation moves the key a new
browser subscribes under and never the key an old one is bound to: a subscription goes on being pushed to
until its key retires, and is then worth nothing, a push service refusing what any other key signs.

## The subscription

The page is `/account/notifications`, one of [the account pages](account.md). It lists the browsers of the
person that the provider can reach, each with the name its owner gave it, when it was added and when it was
last pushed to, and it marks the browser reading the page when that browser is one of them.

1. Opening the page registers the service worker of the application, `/push-worker.js`, served at the root so
   that its scope covers the pages it opens. It registers it each time, a browser being able to lose its worker
   and keep its subscription.
2. The button asks the person for permission, subscribes to the push service of their browser under the
   application server key, and posts what the subscription carries to `POST /account/notifications`: the
   endpoint, the `p256dh` key and the `auth` secret of the browser (RFC 8291 §3), and a name.
3. The provider keeps it against the key the browser was handed. A browser that subscribes again hands back
   the endpoint it already had, and that is the same browser: its row is what changes, and a row its owner had
   taken out is in use again.

The endpoint is taken as the browser gave it, and refused unless it is `https`; the two keys are refused
unless they are base64url; a name longer than 255 characters is dropped. A browser is renamed at
`POST /account/notifications/{id}/name` and taken out at `POST /account/notifications/{id}/revoke`, which keeps
the row, marked revoked.

The endpoint and the name are sealed in their columns, and a browser is recognised by the SHA-256 of its
endpoint, which carries the unique constraint with the person.

[:beffroi-arrow-right: Persistence](persistence.md)

## What a notification carries

Two messages reach a person this way, a request that waits for their answer and a change to the ways their account
signs in. Each is put on the lane of notifications, which hands it to the channels the application wires for it,
web push among them while a subject is named: the only one for a change to the ways in, and one of three for a
request that waits, beside mail and SMS. Every browser the person subscribed is pushed to, and each push carries
three strings and nothing else, `title`, `body` and `url`, in the language of the record of the person when the
deployment serves it, and in the default language otherwise.

No identifier and no link that acts: the notification says that something waits or changed, and the person
goes to a page of the provider they already know, where what it is about is found by who they are. The service
worker shows the notification until it is dismissed, and a tap opens that page, or brings forward a window
already on it.

The payload is encrypted to the two keys the browser gave in `aes128gcm` (RFC 8291 §4), padded to 1024 octets
before it is encrypted, so that a push service learns nothing of a payload that fits in them, not even how long a
binding message or a contact was. A longer one is sent at its own length: a name or a contact written outside ASCII
can make one, each such character being escaped in six octets or more. The request is signed by the application
server key the subscription is bound to, with the subject as its `sub` (RFC 8292 §2.1). It is sent with
`Urgency: high` (RFC 8030 §5.3), and a `TTL` that is the time the message is still worth delivering, which each
message below names (RFC 8030 §5.2), and never less than zero. The provider follows no redirection a push service
answers with.

### A request waits for an answer

When a client makes a backchannel authentication request that names a person, the provider answers the client and
puts the message that tells the person on the lane. A person who has subscribed no browser is pushed nothing: a
mail reaches them when the deployment names a transport and a sender and their address is marked verified, and a
text when it names the DSN of Sweego, the provider of texts the image carries, and their number is marked
verified, as [backchannel authentication](../../developers/oidc/grants/backchannel-authentication.md#reaching-the-person)
says. The request waits where requests are answered.

| Member | What it says |
|---|---|
| `title` | The name of the tenant |
| `body` | The name of the client and what it asks the person to approve, a sign-in or the binding message the client wrote when it wrote one, and that the answer is given in their account |
| `url` | The page of the account where waiting requests are answered, `/account/approvals` |

It is worth delivering until the backchannel request expires.

### A way of signing in changed

When a way of signing in is added to an account or taken away from it, its password is changed, a link to add a
passkey to it is issued or its backup codes are renewed, the provider puts the message that tells its person on
the lane once the act is done, whoever did it. [Credentials](../../administrators/people/credentials/index.md#what-the-person-is-told)
say which acts are told. Every browser the person subscribed is told, the one the change was made from
included when it is one of them: what the provider could tell that browser by, its session or a cookie,
whoever took the session holds as well. A person who has subscribed no browser is told nothing, and finds the
change on the page of their acts.

| Member | What it says |
|---|---|
| `title` | The name of the tenant |
| `body` | What changed and when, on the clock of the person with its zone named, then what to do if it was not them: open their account, and contact the tenant by the contact [it gives](../tenant/tenants.md#the-contact-it-gives-its-people) when it gives one |
| `url` | The home of the account, `/account` under the issuer, a page that acts on nothing |

In English, what changed is one of these sentences:

| Act | What the body says |
|---|---|
| `credential.enrolled` | "A passkey was added to your account on" and the date; "An authenticator app was" or "A password was" in place of "A passkey was" for the other kinds |
| `credential.revoked` | "A passkey was removed from your account on" and the date; "An authenticator app was" for the other kind |
| `password.changed` | "The password of your account was changed on" and the date |
| `enrolment_ticket.issued` | "A link to add a passkey to your account was issued on" and the date |
| `backup_codes.renewed` | "The backup codes of your account were renewed on" and the date |

It is followed by "If it was not you, open your account and contact" and the contact of the tenant, or by "If
it was not you, open your account." when the tenant gives none. The message is worth delivering as long as the
journal keeps the act it tells of, `BEFFROI_JOURNAL_RETENTION` days after it happened, which is as long as the
page of the acts of the account shows it.

## What comes back

| The push service answers | What the provider does |
|---|---|
| `2xx` | The push was taken. The row records when this browser was last pushed to. What the push service does with it afterwards, the provider never learns |
| `404` or `410` | The subscription is gone (RFC 8030 §7.3). The row is taken out of use, revoked, and nothing is pushed to it again |
| Anything else, or no answer within the timeout | This attempt failed, the subscription is left as it is |

A subscription whose application server key has retired is treated as gone without asking the push service,
which would refuse a request signed by any other key. When no browser of the person was reached and at least
one push failed, the message goes back to the lane, which sends it again after the waits of its schedule; one
browser reached is a person told, and the message is done. A request that waits goes back only when no other
channel reached the person either, and its retry calls every channel again.

[:beffroi-arrow-right: The lane of notifications](messenger.md#the-contract-of-the-provider)

## What the deployment allows

The scripts the page loads are served by the application from the origin of the provider, the page posts the
subscription back to it, and the service worker is a script of that origin too. The `Content-Security-Policy`
the application serves the pages of the account, from its `config/packages/nelmio_security.yaml`, allows
them: it names `'self'` in `script-src`, `connect-src`, `worker-src` and `form-action`.
