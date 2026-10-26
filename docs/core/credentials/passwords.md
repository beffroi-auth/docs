---
title: Passwords
description: What a password has to be, the list of compromised values it is compared against, the typed hash it is stored as, and the order of a login by password.
---

# Passwords

A person holds one password at most. It proves `pwd` (RFC 8176 §2), it is replaced and never revoked, and it is
stored as a hash that names the algorithm that produced it, so several algorithms coexist and a hash made by an
older one is replaced the next time the person signs in. What a password has to be is a rule of the core and not
an option: an option to lower it would be the option to do it wrong.

## Setting one

An operator writes the password of a person, asked twice on the terminal without being shown:

``` bash
bin/console beffroi:user:set-password alice
```

With `--password-stdin`, the command reads the password from the standard input, up to the end of its first
line, for a provisioning script. A password is never an argument nor an option, which a shell would keep in its
history, and a command run without a terminal and without `--password-stdin` is refused. The command replaces a
password the person already holds, and ends none of their sessions.

A person replaces their own on [the password page of their
account](../../symfony-bundle/account.md#what-the-password-page-says): they type the one in use, which is
verified, then the one they want, twice. A password that is not the one in use is refused, and so is the one they
already hold; every other browser signed in as them is signed out, and the one they asked from stays. Typing the
wrong password there costs nothing against the attempts of the login, since only somebody signed in as that
person can try.

Both refuse what the rules below refuse, and both refuse to pose a password at all where the [floor of the
tenant](../tenants.md#the-floor-of-its-logins) reads nothing a password proves.

## What a password has to be

A prospective password is refused rather than warned about when it is too short, longer than 4096 bytes, too easy
to guess, or held by a list of compromised values. Nothing else is asked of it: it is never refused for holding
no digit, no capital or no symbol, the composition rules NIST SP 800-63B §3.1.1.2 asks a verifier not to impose.

**How short is too short is two numbers**, as NIST SP 800-63B §3.1.1.2 makes it, and the floor of the logins of
the tenant decides which one applies:

| The floor of the tenant | The length a password has to reach |
|---|---|
| `single_factor`, a password being the whole of a login | fifteen characters |
| `two_factors`, a second factor going with it | eight characters |

A floor that reads nothing a password proves, `phishing_resistant` or `phishing_resistant_hardware`, holds no
password at all. The length is counted in characters, each code point one, and the page, the console and the
core read the same number. A password already stored is left as it is when the floor moves from one of those two
to the other, since a hash says nothing of the length behind it; a floor that holds no password forgets it, row
and hash. Both numbers are in the code and not in a configuration.

**How easy to guess is an estimate of the search space**, counted over the bytes of the password. The pool is
the sum of the alphabets the password draws from, ten for the digits, twenty-six for the lower-case letters,
twenty-six for the capitals, thirty-three for the other printable characters, thirty-three for the control
characters and 128 for the bytes beyond ASCII. Each distinct byte is worth the base-2 logarithm of that pool, and
each byte written again the logarithm of the number of distinct ones. Under sixty bits, the password is refused.
The length and the estimate are two rules and neither absorbs the other: the estimate is what refuses
`passwordpassword`, or one letter typed sixteen times, which no length catches.

**Held by a list of compromised values** is the rule §3.1.1.2 puts first, and the next section.

## The list of compromised passwords

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    passwords:
        breached:
            endpoint: 'https://api.pwnedpasswords.com/range/'
            timeout: 2.0
```

| Option | Default | What it decides |
|---|---|---|
| `endpoint` | empty | A range endpoint in the shape of Pwned Passwords, to which the first five hexadecimal characters of the SHA-1 of a password are appended. Empty, nobody is asked |
| `timeout` | `2.0` | How long one request to the list may take, in seconds, the whole exchange; 0.1 at the least |

**The list is asked by range.** The first five hexadecimal characters of the SHA-1 of the password go out, the
thirty-five that are left are compared locally against every suffix the range answers, the answer is asked
padded so that its length says nothing of the range either, and no API key is needed. Nothing of the person who
typed it goes with the request.

**An unknown is a refusal.** A list that does not answer in time, answers a status other than `200`, or answers
a body that is not a range is not a clean answer: nothing is written, and whoever posed the password is told to
pose it again. A password the list counts is refused, and how many times it counts it is not said.

**A deployment that names no endpoint asks nobody** and poses passwords on the rules of the core alone, no
password and no prefix of one ever leaving it. On the page of the account, the list is asked last, after the
password in use was verified and found different from the one posed, so a person who mistyped is answered
without anything leaving.

## A password already in use

A password that passed every rule the day it was written turns up in a list published a month later. So, after a
login verified the password, a login that goes on to a code included, the SHA-1 of what was typed is handed to a
lane that no sign-in waits on, when the deployment names a list and the password was not looked up in the last
thirty days. What the lane learns is written on the password: found, with the date, or not found. A list that
could not be asked writes nothing: the lane tries again, the password stays due, and the next login asks again.

What the list was found to hold is read on [the password page of the
account](../../symfony-bundle/account.md#what-the-password-page-says) rather than in the one request that
noticed it. Every later login that serves no authorization request of OpenID Connect sends the person there
before the page that was waiting for it, whatever that login used, a password, a code or a passkey, and the
single sign-on of a SAML service provider included, until the password is replaced; once it is, the browser goes
on to the page that was waiting. A new password carries no mark. A login that answers an authorization request
of OpenID Connect is not diverted.

## How it is stored

A hash is a document of three members: the name of its algorithm, the encoded hash, and the parameters an
imported format keeps apart from the digest. A name nothing wired accounts for makes a row this deployment cannot
read, refused where the row is read rather than taken for an algorithm nobody chose.

| Algorithm | What the bundle does with it |
|---|---|
| `argon2id` | Makes every new hash, with the parameter set of RFC 9106 §4: 64 MiB of memory and four lanes, and the four passes PHP takes by default, one more than that set asks. The hasher refuses parameters below these |
| `argon2i`, `bcrypt` | Verifies a hash of them, then stores the password again as `argon2id` at the next successful login |
| `pbkdf2-sha256`, `pbkdf2-sha512` | Reads the hash back and names it. No hasher the bundle wires verifies one |

A hash that is not of the algorithm and the parameters the hasher makes, another algorithm or other parameters,
is replaced at the next successful login, and the act `password.rehashed` goes to the journal of the person: the
password did not change, its hash did.

No command takes a hash: a password is set from its value, and a person who has none is given a passkey by an
[enrolment ticket](passkeys.md#a-first-passkey-from-a-ticket) or signs in through their organisation. An
algorithm is a class implementing `PasswordAlgorithmInterface`, tagged `beffroi.password_algorithm`; a hasher of
algorithms is a class implementing `AlgorithmPasswordHasherInterface`, tagged `beffroi.password_hasher`. The
registry hands each hash to the hasher that supports its algorithm, and every new hash to the hasher that supports
the first algorithm wired.

## The order of a login

The login page and the use case of the core play one order, written once:

1. A tenant whose floor reads nothing a password proves refuses every password, before anybody is named and
   without paying a hash, the answer depending on nobody's account.
2. The person is named by the username typed. A username nobody holds is refused.
3. The attempt is counted against that person: five in a sliding window of one minute, the sixth refused. A
   username nobody holds is counted nowhere, so a limiter cannot be filled with what an attacker types.
4. The hash is verified. A refusal reached before this step, an unknown username, too many attempts or a person
   who holds no password, still pays the verification of a hash the hasher made of a value nobody knows, so the
   time of the answer does not say whether the account exists.
5. A disabled account, and a person of a federated domain, are refused after the password, as a wrong password is.
6. The count of attempts is emptied, the password dated as used and stored again when its hash is not the one the
   hasher makes, and the act `password.used` written. A person who holds an active TOTP is then held at the code page rather than signed in:
   [authentication sessions](../authentication-sessions.md#opening-one) say what follows.

Every refusal of these steps is announced with the request it came from, and the person is told the same thing
whatever the reason. A form without its token, or with an empty field, is refused by the login page before any of
them: it is not an attempt on an account, and costs the person it names nothing.

## A person of an organisation

A person whose address is of a domain an [upstream identity provider](../../saml/federated-sign-in.md) answers
for has no password here. One is neither set for them, by the console or on the page of their account, nor
accepted from them, and a password they held before their domain was federated is refused at the login and can no
longer be replaced.
