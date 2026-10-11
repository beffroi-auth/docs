---
title: Messenger
status: draft
description: Which writes are asynchronous, and which the protocol waits for.
---

# Messenger

No write is synchronous unless the protocol needs its result in the same request, and every exception is
listed in the Messenger configuration with the reason it is one. Messages are commands, queries, events or
explicitly synchronous messages, and a handler calls a use case rather than holding logic of its own.

**The buses, their middleware and where each kind of message is sent are a contract the bundle prepends**
to the Messenger configuration of the application, not a preference of whoever installs it: an
installation that wires them itself and turns the default middleware off, or gets the Doctrine transaction
middleware wrong, breaks the asynchronous half of the provider quietly. What is left to an application is
its transports, and the lanes fall back to the database, so a new installation needs no broker to work.

**The body of every message leaves the process sealed.** What a column seals, a queue may not carry in
clear: a message is sealed as a JWE towards the encryption key of the tenant, so what a broker, the table
of a transport or the failure transport holds is worth nothing without the key management service. The
sender holds the public half only and asks the key management service for nothing; the consumer unseals
the private half once per process. That key is a key of the tenant like the others, rotated and rewrapped
like them, and it is never published in the JWK Set: a key at the JWK Set is a key any reader of the
discovery document could seal a body under.

The transport headers carry the tenant, so a consumer knows which key to ask for before it touches the
body and a failed message can be read without being opened. What decides is the protected header of the
JWE, which is the authenticated data: a header swapped in transit makes the unsealing fail rather than
succeed under another scope.

**What time does on its own is one recurring message per step**, handled on the command bus like every
other write, so a deployment that runs the worker runs them.

This page will describe the transports, the queues, what runs where, and what happens when the broker is
down.
