---
title: Web push
description: Reaching a person through the push service of a browser they signed in with (RFC 8030), what a notification carries, and what becomes of it.
---

# Web push

A deployment that names a push subject reaches a person through the push service of a browser they signed in
with (RFC 8030): the person subscribes that browser on a page of their account, and the provider pushes to it
when a request waits for their answer. It is how a backchannel authentication request (CIBA Core §7) reaches
the person it names without a second application. Nothing in a notification names the request it is about.

## Turning it on

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    web_push:
        subject: 'mailto:operator@op.example.com'
```

| Option | Default | What it decides |
|---|---|---|
| `subject` | none | The `sub` of the token the provider signs for a push service (RFC 8292 §2.1): a `mailto:` or `https:` URI at which a push service can reach the operator of the deployment. Naming one is what turns web push on |
| `timeout` | `3.0` | Seconds one push to one push service is given, connection included, so that a push service that hangs does not hold a worker |

**Without a subject, nothing of it is wired.** No push leaves the deployment, the tenant draws no
application server key, and the page where a browser would subscribe says that the provider does not tell
browsers. A key drawn before the subject was taken away is read by nothing until a subject is named again.

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

1. Opening the page registers the service worker of the bundle, `/push-worker.js`, served under the path the
   routes are mounted at, so that its scope covers the pages it opens. It registers it each time, a browser
   being able to lose its worker and keep its subscription.
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

When a client makes a backchannel authentication request that names a person, the provider answers the
client and puts the message that tells the person on the lane of notifications. The lane hands it to every
channel the deployment wires; web push is the one the bundle ships, wired when a subject is named. A person
who has subscribed no browser is told nothing, and finds the request where requests are answered.

Every browser the person subscribed is pushed to, and each push carries three strings and nothing else, in
the language the person reads:

| Member | What it says |
|---|---|
| `title` | The name of the tenant |
| `body` | The name of the client and what it asks the person to approve, a sign-in or the binding message the client wrote when it wrote one, and that the answer is given in their account |
| `url` | The page of the account where waiting requests are answered, `/account/approvals` |

No identifier of the request and no link that answers it: the notification says that something waits, and
the person goes to a page of the provider they already know, where the request is found by who they are. The
service worker shows the notification until it is dismissed, and a tap opens that page, or brings forward a
window already on it.

The payload is encrypted to the two keys the browser gave in `aes128gcm` (RFC 8291 §4), padded to 1024 octets
before it is encrypted, so that a push service learns nothing of it, not even how long the binding message
was. The request is signed by the application server key the subscription is bound to, with the subject as
its `sub` (RFC 8292 §2.1). It is sent with `Urgency: high` (RFC 8030 §5.3), and a `TTL` that is the time left
before the backchannel request expires (RFC 8030 §5.2), and never less than zero. The provider follows no
redirection a push service answers with.

## What comes back

| The push service answers | What the provider does |
|---|---|
| `2xx` | The push was taken. The row records when this browser was last pushed to. What the push service does with it afterwards, the provider never learns |
| `404` or `410` | The subscription is gone (RFC 8030 §7.3). The row is taken out of use, revoked, and nothing is pushed to it again |
| Anything else, or no answer within the timeout | This attempt failed, the subscription is left as it is |

A subscription whose application server key has retired is treated as gone without asking the push service,
which would refuse a request signed by any other key. When no browser of the person was reached and at least
one push failed, the message goes back to the lane, which sends it again after the waits of its schedule; one
browser reached is a person told, and the message is done.

[:beffroi-arrow-right: The lane of notifications](messenger.md#the-contract-the-bundle-prepends)

## What the deployment allows

The scripts the page loads are served by the bundle from the origin of the provider, the page posts the
subscription back to it, and the service worker is a script of that origin too. A deployment that writes its
own `Content-Security-Policy` for the pages of the account allows them: the standalone application's names
`'self'` in `script-src`, `connect-src`, `worker-src` and `form-action`.
