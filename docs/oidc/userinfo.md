---
title: UserInfo
status: draft
description: What a client reads about the person, OIDC Core §5.3.
---

# UserInfo

UserInfo answers the claims the access token allows, for the person it was issued for, as JSON or as a signed
and optionally encrypted JWT. It is the one endpoint where the answer depends on the token and on the consent
behind it rather than on the request.

Every answer is an act of the journal of that person, `userinfo.answered`, naming the client it was given to:
it is one of the two reads that hand a personal datum to a third party. It is written once the answer exists,
so a request that could not be answered is no line of it.

This page will describe the request, the claims returned, and the signed and encrypted responses.
