---
title: Persistence
status: draft
description: The Doctrine mapping, the migrations, and the DBAL types.
---

# Persistence

The model is mapped with XML, outside the entities, and a value object a column holds whole goes in one
column with a DBAL type of the bundle that reads it back through the object's own constructor. An
embeddable would fix the type of each of its fields once for the whole model, so the same kind of value
could not be sealed in one table and readable in another, which is why there is one embeddable in the
mapping and not a family of them: the authorization request, embedded by one entity, whose first field is
an entity no mapping carries.

This page will describe the schema, the migrations, the types, and what a sealed column changes about a
query.
