---
title: Messenger
description: Which writes leave the request, the buses and lanes the bundle prepends, the worker, the timed steps, and the seal on every message.
---

# Messenger

What the protocol or the page needs in the same request, a code or a token issued, a session opened, a
credential dated by the login that used it, a passkey renamed, is written by the use case in that request. The
rest travels on a lane and a worker carries it out: the acts of the journal, the enrichment of where a request
came from, the revocations that follow the end of a session, the calls to clients and push services. No
message of the bundle travels on the synchronous transport. The buses, their middleware, where each message
goes and how it is written are a contract the bundle prepends; what an application owns is its transports.

## What leaves the request

Every message of the bundle implements one marker, every event of the packages one interface, and that is
what decides where it goes.

| Marker | Routed to | What it is |
|---|---|---|
| `Beffroi\Bundle\Message\Command` | `async_priority_medium` | A write whose result the request does not need |
| `Beffroi\Bundle\Message\Event`, and every event of the core, of OpenID Connect and of SAML | `async_priority_low` | Something that happened. The events of the packages are routed by the interface they all implement, so an event added to one of them leaves the process without a line of configuration |
| `Beffroi\Bundle\Message\Notification` | `async_notifications` | Something the provider carries to a third party it does not own |
| `Beffroi\Bundle\Message\Query` | `sync` | A read |
| `Beffroi\Bundle\Message\SyncMessage` | `sync` | A write the protocol needs the result of before it answers |

No message of the bundle implements `Query` or `SyncMessage`. A class implements one marker and never two:
Messenger sends a message to every transport its class, its parents and its interfaces are routed to, so a
message with two markers would be handled twice. The core announces its events in PSR-14, and its dispatcher
puts each one on `event.bus`, once the handler in progress has committed when one is raised inside a handler:
the lane carries it to a worker, and nothing listens to an event in the process that raised it.

What the lanes carry out:

| On | What is done there |
|---|---|
| `async_priority_low` | Every act written to the journal; where a session was seen from, enriched; the tokens of an ended session revoked, and again for a refresh that was in flight; the clients of an ended session handed a logout token to carry; the date a client was last used; what a client was given of a person; the archive a person asked for, built; the part of a SAML service provider in a session, recorded; the client of an answered backchannel request handed its notification to carry |
| `async_priority_medium` | A password that just signed somebody in, looked up in a list of compromised passwords; the language a person chose, written on their account; and every step of [the schedule](#what-time-does-on-its-own) |
| `async_notifications` | A logout token posted to a client (Back-Channel Logout 1.0 §2.5), a backchannel request whose client is told it was answered (CIBA Core §10.2), a person told that a request waits for them, through the channels the deployment wires, [web push](web-push.md) among them |

## The contract the bundle prepends

**The buses.**

| Bus | Middleware |
|---|---|
| `command.bus`, the default bus | The default middleware of Messenger, then `router_context`, `doctrine_ping_connection`, `doctrine_close_connection` and `doctrine_transaction` |
| `event.bus` | The default middleware, with `allow_no_handlers`: an event nothing listens to is announced all the same |
| `query.bus` | The default middleware |

`doctrine_transaction` makes a handler one unit of work, and the default middleware, which no bus turns off,
is what has an event announced from a handler leave once that handler has committed. `router_context` gives
a worker the context of the request that dispatched the message, so that a URL built there is an absolute URL
of the issuer, and the two connection middleware are what let a worker run for days. This is why the bundle
writes the buses and an application does not: one that wired them itself and got either of the first two
wrong would break the asynchronous half of the provider, and nothing in a browser would show it.

**The transports.**

| Transport | DSN | Tried again |
|---|---|---|
| `sync` | `sync://` | Not at all |
| `async_priority_high`, `async_priority_medium`, `async_priority_low` | `%env(BEFFROI_MESSENGER_DSN)%`, `doctrine://default` when the variable is not set | Four times, one second before the first, each wait four times the one before, thirty seconds at most |
| `async_notifications` | The same | On the schedule of `Beffroi\Bundle\Messenger\NotificationRetryPolicy`, which `beffroi.back_channel_logout` sets: by default two seconds before the first, each wait three times the one before, sixty seconds at most, the waits exact |
| `failed`, the failure transport | `doctrine://default?queue_name=failed` | |

The failure transport is the database whatever the lanes are on, a failure transport kept on the broker that
failed being one nobody reads. The contract routes no message to `async_priority_high`.

**The serializer.** `beffroi.messenger.serializer` is the default serializer of every transport, the failure
transport included: what it writes is the subject of [the last section](#what-leaves-the-process-is-sealed).

## What the application writes

**Nothing, to start.** Every lane is the database, through the default connection, and a provider runs with
no broker. `BEFFROI_MESSENGER_DSN` moves every lane to one DSN at once.

**Its transports, to put lanes on a broker.** A transport the application declares under the name of a lane
keeps the application's settings, the prepended configuration being merged first. The standalone application
runs RabbitMQ and binds each lane to a queue of its own on one exchange, which is the part of a transport only
a deployment knows:

``` yaml title="config/packages/messenger.yaml"
messenger:
    transports:
        async_priority_high:
            dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
            options:
                exchange: { name: beffroi_messages, type: direct, default_publish_routing_key: high }
                queues:
                    beffroi_messages_high: { binding_keys: [high] }
        async_priority_medium:
            dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
            options:
                exchange: { name: beffroi_messages, type: direct, default_publish_routing_key: medium }
                queues:
                    beffroi_messages_medium: { binding_keys: [medium] }
        async_priority_low:
            dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
            options:
                exchange: { name: beffroi_messages, type: direct, default_publish_routing_key: low }
                queues:
                    beffroi_messages_low: { binding_keys: [low] }
        async_notifications:
            dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
            options:
                exchange: { name: beffroi_messages, type: direct, default_publish_routing_key: notifications }
                queues:
                    beffroi_messages_notifications: { binding_keys: [notifications] }
```

The block is under `messenger` and not `framework.messenger`: in Symfony 8.2 the component has an extension
of its own, and a block written under `framework` does not override what the bundle prepends to
`messenger`. The standalone application sets every lane to `sync://` in its test environment, where the
writes are played inside the request.

!!! warning "The notifications keep the retry policy of the bundle"

    The schedule of the lane is the one `beffroi.back_channel_logout` sets: `retries`, six by default,
    `retry_delay`, two seconds, `retry_multiplier`, three, and `retry_max_delay`, sixty seconds, with the
    `timeout` of one send, five seconds. These numbers make the budget a logout token is written for: with the
    defaults, waits of 2, 6, 18, 54, 60 and 60 seconds before the six retries, two hundred seconds in all, and
    five seconds for each of the seven sends they count. That budget is the `exp` of the token, and the key
    that signed it stays in the JWK Set at least that long once it retires. It bounds the token and not the
    sending: a client still out of reach when the budget has run out may be sent the token again,
    `retry_max_delay` seconds apart, and what it receives then is past its `exp`.

    A deployment that routes the notifications to a lane of its own, or names another retry service on
    `async_notifications`, keeps a provider that works and two figures that no longer agree: a client reached
    on a late retry refuses a token it can no longer verify, and the person stays signed in there.
    `beffroi:doctor` says so. Writing the four numbers of a retry strategy on the lane of the bundle changes
    nothing: the service the bundle prepends survives the merge, and the component prefers a service to its
    numbers.

## The worker

The standalone application runs one worker, which consumes the schedule and then the lanes, the
notifications first so that a relying party learns of a logout without waiting behind a batch of
enrichments:

``` bash
bin/console messenger:consume scheduler_beffroi async_notifications async_priority_high async_priority_medium async_priority_low --time-limit=3600 --memory-limit=256M
```

One process at a time consumes `scheduler_beffroi`: the steps of the schedule are idempotent, not
concurrent. The lanes may have more consumers than one. A worker asks the key management service once per key
it opens and keeps the key for as long as it lives, which is what keeps the service off the path of every
message.

## What time does on its own

The schedule of the bundle, `beffroi`, is one recurring message per step. Its transport is
`scheduler_beffroi`, and the bundle prepends `use_messenger_routing: true` to the scheduler, so each message is
routed by its class like every other: the worker that holds the clock only says when, and the step is handled
on `async_priority_medium`.

| Step | Every | What it does |
|---|---|---|
| `AdvanceKeyLifecycle` | Minute | Stages a successor for every key past its age, activates every staged key whose delay has elapsed, retires every key past its retirement date |
| `ForgetTheRecordsThatAreDead` | Hour | Drops the rows of the protocol that nothing alive needs any more |
| `ForgetTheExpiredArchives` | Hour | Forgets the archives of persons past their week |
| `RemoveUnusedClients` | Hour | Deletes the clients that registered themselves and nobody uses |
| `RefreshTheSamlMetadata` | Hour | Reads again the metadata of the SAML peers of both roles |
| `ForgetTheActsPastTheirRetention` | Day | Forgets the acts of the journal past its retention, and the disclosures with them |
| `ForgetTheChangesPastTheirRetention` | Day | Forgets the changes of claims past their retention |
| `RefreshTheAddressDatabases` | Week | Downloads the databases of addresses again, for a deployment that names a licence key |

A deployment whose worker does not consume the schedule rotates nothing on its own, and `beffroi:keys:list
--check` fails on the first key that works past its age with nothing staged behind it, naming the transport
to consume.

[:beffroi-arrow-right: The rotation of a key](console-commands.md#rotating-a-key)

## What leaves the process is sealed

What a column seals, a queue does not carry in the clear. **The body of every message is a compact JWE**,
sealed to the key the tenant keeps for it, `MESSAGE-SEAL`, under `ECDH-ES+A256KW` and `A256GCM`: what a broker
keeps on its disk, what the table of a transport holds and what waits in the failure transport is worth
nothing without the key management service.

- **The sender asks the key management service for nothing.** It seals to the public half of the newest key
  of that algorithm in service, a staged one included, so the event that announces the first key of a tenant
  is sealed to that key.
- **The consumer opens the key the body names**, by its `kid`, once per process. A body sealed to a key that
  has retired since does not open, which bounds how long a message may wait in a queue.
- **The key is never published in the JWK Set**: a key published there would let any reader of the discovery
  document seal a body the provider opens. It rotates like every other key of the tenant.
- **A tenant that holds no such key writes no message at all**, rather than one in the clear, which is why it
  is the first key a tenant is given.

**The headers of the transport say what the message is without opening it**: `type`, the class of the
message, and one `X-Message-Stamp-` header per class of stamp, among them the slug of the tenant the message
was written for. So `messenger:failed:show` names, dates and explains a failed message without its body
being opened, and nothing of a person is in any of them. What decides is not a header: the protected header
of the JWE names the tenant as well, and being the authenticated data of the body, a header swapped on a
transport makes the opening fail rather than succeed somewhere else.

**A body that does not open is a failure of that message**, which goes to the failure transport with the
headers it arrived with: a body that is not a JWE, a message written for another tenant than the one the
process serves, a key that has retired, a body that opens as another class than its header names. A key
management service that does not answer is a failure of the process and not of the message, and is not turned
into a failed message nobody would replay.
