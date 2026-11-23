---
title: The terminal client
description: Install the client of the administration API on your machine, connect it to an instance, and administer a tenant from your terminal.
---

# The terminal client

`beffroi-tui` is the client of the administration API of an instance, which runs in a terminal on your own
machine. It is a client of the provider like any other: it signs you in through the provider, talks to the
instance over HTTP, and installs none of the packages of the provider. The operator of the instance serves the
API on [a host of its own](../operators/application/deployment.md#the-host-of-the-administration-api) and names
the groups whose members administer the tenant; this page starts from there.

## Installing it

Each [release](https://github.com/beffroi-auth/beffroi/releases) carries the client as four files:

| File | Runs on |
|---|---|
| `beffroi-tui.phar` | PHP 8.4 or later. A PHP that lacks an extension the client needs is refused before the client starts, with the name of that extension |
| `beffroi-tui-linux-x86_64` | Linux on x86_64, without PHP: the file carries its own |
| `beffroi-tui-linux-aarch64` | Linux on arm64, without PHP |
| `beffroi-tui-macos-aarch64` | macOS on Apple silicon, without PHP |

There is no Windows build: the client drives the terminal through `stty`.

`SHA256SUMS` holds the digests of the four files, and `SHA256SUMS.asc` is its signature by the key that signs
the release tags, `Beffroi releases <releases@beffroi.tech>`, of fingerprint
`FAFA 4D7E 39BA B0AE 08EE  4439 544F 6C79 29EA 07AF`. The client carries that key to verify its own updates.
Check the file you downloaded before you run it:

=== "Linux"

    ``` bash
    curl -fsSL https://raw.githubusercontent.com/beffroi-auth/beffroi/HEAD/apps/tui/resources/release-signing-key.gpg | gpg --import
    gpg --verify SHA256SUMS.asc SHA256SUMS
    sha256sum --check --ignore-missing SHA256SUMS
    chmod +x beffroi-tui-linux-x86_64
    ```

=== "macOS"

    ``` bash
    curl -fsSL https://raw.githubusercontent.com/beffroi-auth/beffroi/HEAD/apps/tui/resources/release-signing-key.gpg | gpg --import
    gpg --verify SHA256SUMS.asc SHA256SUMS
    shasum -a 256 --check --ignore-missing SHA256SUMS
    chmod +x beffroi-tui-macos-aarch64
    ```

`gpg --verify` reports a good signature from `Beffroi releases <releases@beffroi.tech>`, and the check of the
digests reports the file you downloaded `OK`. The commands on this page call the client `beffroi-tui`,
whatever name you keep it under.

## Connecting it to an instance

### What you are given

Registering the client takes three values, which the operator of the instance gives you, or another
administrator of the tenant:

| Value | What it is |
|---|---|
| The issuer of the tenant | An `https://` URL, exactly as the discovery document of the tenant names it |
| The identifier of its administration API | The value the deployment gives `BEFFROI_TENANT_ADMINISTRATION_RESOURCE`, an absolute `https://` URI without a query or a fragment (RFC 8707 §2). The provider announces it nowhere, so somebody tells you |
| An initial access token issued for the administration | Issued by the operator with `bin/console beffroi:client:token:issue <name> --administration`, or by an administrator in [the Clients section](#clients-and-initial-access-tokens) with `administration` set to `yes` |

Of the clients that register themselves, only one registered with such a token is given the administration API,
so the tenant registers its clients with initial access tokens, `BEFFROI_REGISTRATION_MODE` set to `initial_access_token` ([the variables of
registration](../operators/application/configuration.md#registration)). A client registered any other way is
refused the API at the sign-in.

### Registering this machine

``` bash
beffroi-tui register https://op.example.com https://admin.example.com
```

`register` draws an ES256 key on your machine and registers the client with its public half (RFC 7591), a
confidential client that authenticates with `private_key_jwt` and comes back to the loopback interface,
`http://127.0.0.1:<port>/callback` (RFC 8252 §7.3). It asks for the initial access token without echoing it, or
reads it from `BEFFROI_TUI_INITIAL_ACCESS_TOKEN`, and never takes it on the command line. It then prints the
client identifier, the redirect URI, the administration API, the thumbprint of the key and the path of the
profile.

| Option | What it does |
|---|---|
| `--profile` | The name the registration is kept under, `default` when it is not given: lowercase letters, digits, `-` and `_`, 63 at most. One profile per instance you administer |
| `--client-name` | The name the tenant lists the client under, `Beffroi TUI on` followed by the name of your machine when it is not given |
| `--port` | The port of the loopback interface. A port free at registration is taken otherwise, and kept |
| `--cafile` | A file of certificate authorities the instance is trusted under, in place of those of the system. A file the group or others may write is refused |

### The profile

The profile is the file `$XDG_CONFIG_HOME/beffroi/tui/<profile>.json`, or `~/.config/beffroi/tui/<profile>.json`
when that variable is not set or is not an absolute path. It holds the issuer, the client and its redirect URI, the private key of the
client, the administration API, what the provider handed the client to manage its registration (RFC 7592), and
the path given to `--cafile`. Its directory is created for you alone and the file is readable by you alone; a
profile the group or anyone else may open is refused until `chmod 600` closes it. No token of a sign-in is ever
written to it.

A profile is never written over, since the registration it held would be left at the instance with nobody
holding its key. Each machine registers on its own: a key never leaves the machine it was drawn on, and deleting
the client of one machine leaves the others working.

The instance removes a client that registered itself once it goes unused for as long as the deployment keeps one:
ninety days once it was used and seven days when it never was, unless the deployment says otherwise. Each sign-in
is a use. A machine
whose client was removed registers again: delete its profile, then run `register` with a new token.

### Signing in

``` bash
beffroi-tui
beffroi-tui administer --profile staging
```

Run without a command, the client opens the administration of the profile `default`, and `administer --profile`
opens another. Without the name of the command, the option takes its value after an equals sign,
`beffroi-tui --profile=staging`. The administration needs a terminal to draw itself in.

The home page names the instance, the profile and the version of the client. Enter opens the sign-in of the
instance in the browser of your machine: the program `BROWSER` names, or else `open` on macOS and `xdg-open`
elsewhere. You sign in there with a passkey, at every start of the client, even when the browser holds a session
already, and the browser comes back to the client. When no browser opens, the address of the sign-in is on the
screen. On a machine without a browser, forward the port of the profile from the machine where the browser is,
with `ssh -L <port>:127.0.0.1:<port>` to the machine the client runs on.

The sign-in is the authorization code flow, held to the client side of FAPI 2.0 Security Profile §5.3.3: a
pushed request (RFC 9126) for the administration API as its resource (RFC 8707 §2), PKCE `S256` (RFC 7636 §4.2),
the class `phr` asked as an essential claim (OIDC Core §5.5.1.1), the issuer of the response checked
(RFC 9207 §2.4), and the tokens bound by DPoP under ES256 (RFC 9449). An instance whose metadata do not announce
pushed requests, PKCE `S256`, the class `phr`, the issuer in the response, `private_key_jwt` and DPoP under ES256
is not talked to, and the screen says what is missing.

The tokens are bound to a key drawn when the sign-in starts and held in the memory of the client alone; neither the tokens nor
that key are ever written. While the client runs, it refreshes the access token before it expires, when the
instance handed it a refresh token (RFC 6749 §6); without one, the API refuses the session once the access token
has expired, and the screen asks you to quit and sign in again. Quitting hands the tokens back to the instance
(RFC 7009).

A sign-in that fails leaves the home page with what the instance answered, and Enter starts it again. Three
refusals come with what to do:

| The instance answers | What it means |
|---|---|
| `access_denied` | Your account does not administer the tenant, or you refused the consent |
| `unmet_authentication_requirements` | The sign-in proved no passkey: add one on the page of the passkeys of your account |
| `invalid_target` | This client may not ask for the administration API: register the machine again, with an initial access token issued for the administration and the identifier the deployment names |

### Who may administer a tenant

The instance decides, when it issues the tokens and again at every request the client makes. A request comes
from an administrator when:

- you are a person of the tenant and a member of one of the groups the deployment names in
  `BEFFROI_TENANT_ADMINISTRATORS`, whatever source holds the membership ([who administers the
  tenant](people/groups.md#who-administers-the-tenant));
- you signed in at the authorization endpoint with a passkey, a proof of the class `phr`, whatever the floor of
  the tenant, in a session that has not ended: a password is refused, with a second factor or without;
- the access token is addressed to the administration API, was issued to you and not on your behalf (RFC 8693
  §4.1), and is bound to a key that the request proves again (RFC 9449 §7.1).

The role is read at the moment it is asked. A person taken out of the group, or whose account is disabled, is
refused at the next request, with the tokens already issued. A tenant whose deployment names no group, or no
administration API, has no administrator.

## The screen

Once you are signed in, a header line names the instance and you, with the class you signed in under. The
sections are a column on the left of a terminal 90 columns wide or more, and tabs above the section shown in a
narrower one. The last line says the keys that answer where the focus is.

| Key | What it does |
|---|---|
| ↑ ↓, or ← → on tabs | Choose a section, or move in a table |
| Enter | Go into the section chosen; in a table, open the row chosen; in a field, submit what you typed |
| Tab, Shift+Tab | Move between the navigation and the parts of the section |
| Page Up, Page Down, Home, End | Move in a table by a screen, or to its first or last row |
| Esc | Go back to the navigation; on the navigation, quit |
| r | Read the section shown again |
| q | Quit. Ctrl+C quits from anywhere |

In a field you type in, `r` and `q` are letters. A section is read from the API the first time it is shown and
again when you press `r`, and its heading says when it was read.

A key that asks to make a change says on a line of the section what the change will do: `y` makes it, and any
other key forgets the question. The line then says what the API answered, or why nothing was changed.

The screen speaks English or French, from `LC_ALL`, `LC_MESSAGES` or `LANG`, and asks the pages of the sign-in
in the same language. It draws without colours when `NO_COLOR` is set to a value that is not empty, and never
says a state by a colour alone.

## The sections

Five sections read without changing anything:

| Section | What it shows |
|---|---|
| Instance | The issuer and the administration API, the client this machine is, its redirect URI and the thumbprint of its key, the key the tokens of this run are bound to, the endpoints of the sign-in, and the version of the client with whether a newer release of its line is out. It reads nothing of the API |
| Session | Your name, your subject, the class and the methods you signed in with (`acr`, `amr`), when, and the scope of the access token with the minutes it has left |
| Tenant | Its name, slug, issuer and creation date, [the floor of its logins](../operators/tenant/tenants.md#the-floor-of-its-logins), the groups that administer it, its administration API and how long its journal keeps an act, beside [the classes it answers with](../operators/tenant/tenants.md#the-classes-it-answers-with). [The contact the tenant gives its people](../operators/tenant/tenants.md#the-contact-it-gives-its-people) is set through the administration API, which the client does not do |
| Signing keys | A row per key: its state, marked and worded `■ active`, `□ staged`, `▨ retiring` or `┄ retired`, its algorithm, identifier and use, its dates, and whether an active key is past its age ([the life of a key](../operators/tenant/keys.md#the-life-of-a-key)) |
| Monitoring | The people, clients, open sessions, active and staged keys and messages waiting; each point `beffroi:doctor` looks at, `■ ok` or `■ failed` with what it found; and the acts over what the journal keeps, the failures in the colour of errors ([metrics and health](../operators/application/observability.md#metrics-and-health)) |

### Clients and initial access tokens

The Clients section lists the clients of the tenant by name, identifier and source, with when each was
registered and last used. The view of the initial access tokens lists each one with its state, the
registrations it served of those it allows, when it expires, and whether its clients are clients of the
administration.

| Key | What it does |
|---|---|
| Enter on a client | Shows what it registered, what the registration policy assigned it and what its initial access token gave it |
| `x` on a client | Asks to delete it: nothing it was issued can be used any more. A client the deployment declares, and the one you act through, are refused |
| `i` | Shows the initial access tokens in place of the clients, read again each time |
| `c` | Shows the clients again |
| `n` on the tokens | Opens the form of a new token: its name, how many clients it may register (1), for how many days (30), whether they are clients of the administration (`no`), and the APIs it gives them, separated by commas. Enter on a row types its value, or turns the `yes` over |
| `s` in the form | Issues the token. Its value is shown once, to copy for whoever registers the client, until Enter closes it or the focus leaves it; neither the client nor the instance shows it again |
| `x` on a token | Asks to revoke it: it authorises no more registrations, and the clients it registered stay |

### Mail keys

The Mail keys section lists the keys the mail of the tenant is signed with, each marked and worded `■ current`
or `▨ replaced`, with its format, S/MIME or OpenPGP, its fingerprint, the senders it signs for and its dates.
A deployment that names no sender, `BEFFROI_MAIL_SENDER`, writes no mail, and refuses a key of either format.

| Key | What it does |
|---|---|
| `p` | Asks to generate an OpenPGP key. The instance draws it, and the tenant serves it at `<issuer>/mail/pgp-keys` for whoever verifies the mail. It replaces the current OpenPGP key, which stays published until you remove it |
| `s` | Opens a field for the file of an S/MIME private key in PEM, then one for the file of its certificate followed by its chain, where Enter sets the key. Both files are read on your machine and the key is never shown; a path that names no readable file, a file over 64 KiB, and a private key the group or others may open are refused before anything is sent. The key replaces the current S/MIME key |
| `x` on a key | Asks to remove it. Removing the current key of a format leaves the mail of that format unsigned |

### Users

The Users section reads nobody until you type a username in its first field, `Username:`, and press Enter. The
person is shown with their username, whether they are enabled, their source, groups, subject and claims, beside
their credentials. The second field, `New person:`, creates the username typed, with no credential ([creating
one](people/users.md#creating-one)).

| Key | What it does |
|---|---|
| `c` | Shows their credentials |
| `s` | Reads their open sessions, with the proof, the dates and where each came from |
| `j` | Reads their last acts |
| `a` | Reads the applications they agreed to |
| `x` on a credential | Asks to revoke it ([revoked and forgotten](people/credentials/index.md#revoked-and-forgotten)). A password is replaced, never revoked |
| `x` on an open session | Asks to end it; the applications it signed in to are told ([ending one](people/authentication-sessions.md#ending-one)) |
| `x` on an application | Asks to revoke the consent; an access token already issued stays valid until it expires |
| `t` | Asks to issue the link that lets them add a [passkey](people/credentials/passkeys.md#a-first-passkey-from-a-ticket) |
| `p` | Asks to issue the link that lets them set a new [password](people/credentials/passwords.md#setting-one) |
| `o` | Asks to issue the link that lets them set up an [authenticator application](people/credentials/totp.md#from-a-ticket) |
| `e` | Opens the form of their account: the username, the email address and the phone number with whether each was verified, the claims of OIDC Core §5.1 and the parts of the address. Enter on a row types its value, an empty one taking the claim away, or turns a verification over; `s` saves every change at once ([what an administrator says of a person](people/users.md#what-an-administrator-says-of-a-person)). Leaving the form forgets what it did not save |
| `d` | Asks to disable them, which ends every session of theirs, or to enable them again ([a disabled user](people/users.md#a-disabled-user)). You cannot disable yourself |

A link takes the place of the person, as its text and as a QR code to scan with the device that will use it.
It is valid until the instant the screen says, and the previous link of the same kind stops working. It leaves
the screen when the focus moves, and Enter brings the person back.

### Groups

The Groups section lists the groups of the tenant by name, source, number of members and whether they
administer the tenant, which reads nobody. The members of a group are read only when you ask for them
([groups](people/groups.md)).

| Key | What it does |
|---|---|
| Enter on a group | Reads its members, with the source and the date of each membership |
| `n` | Opens the field `New group:`, where Enter creates the group named |
| `a` | Opens a field for a username, where Enter adds that person to the group chosen or shown |
| `x` on a member | Asks to take them out. The question says so when the group administers the tenant, and you cannot take yourself out of such a group |

## Every act names you

Each change you make through the client is an act of the journal that names you, by the subject of your
account, and the line that says it was done ends with "Logged under your name." Reading a person, their open
sessions, their last acts or the applications they agreed to, and reading the members of a group, are acts of
each person read, which name you as well: the Users and Groups sections say so before the first read. Listing
the groups, the clients and the keys, and reading the tenant and the monitoring, reads nobody
([the journal](../operators/application/observability.md#the-journal)).

## Keeping it up to date

`beffroi-tui --version` prints the release a file was built from, and the home page and the Instance section
say it too. When the administration opens, before any sign-in, a release looks once for a newer release of its
line, `0.1.*` for `0.1.0`, in the GitHub API and without any credential. The screen then names the newer release
with the command that installs it, says the client is the newest of its line, or says the update was not
checked and why, as it does on a machine that cannot reach GitHub. Nothing turns that look off.

``` bash
beffroi-tui self-update
./beffroi-tui-linux-x86_64 self-update      # an executable kept under its own name
```

`self-update` replaces the PHAR or the executable that runs by the same file of the newest release of its line,
and runs the verification above for you. It downloads `SHA256SUMS` and `SHA256SUMS.asc` first, and `gpgv`
checks the signature under the release key the client carries, never one fetched at run time. Only then is the
file downloaded, and it must match its line of `SHA256SUMS`, or nothing is replaced.

- It needs `gpgv` on the `PATH` and write access to the directory the program sits in. It asks for no more
  privileges, so a copy in a directory only root writes to, such as `/usr/local/bin`, is refused, and it has
  no option.
- It never moves to another line, where a `0.x` version may break what it talks to: the next line is a new
  download, checked as above.
- A copy that runs from its sources, as Composer installs it, is updated by Composer, and a build of anything
  but a release does not replace itself.

The client reaches `api.github.com` for the list of the releases and `github.com` for their files, which GitHub
answers with one redirection to the host it stores them on. That redirection is followed once, to an `https`
address only; no other request of the client follows one.
