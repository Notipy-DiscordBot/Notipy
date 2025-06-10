# Notipy Backend

This directory contains the FastAPI server that powers Notipy.

## HTTP 204 Responses
Some endpoints return `204 No Content` when the request succeeds but the database has no information to provide. The call was processed correctly; there is simply nothing to return.

For full setup and usage details, see the [root README](../README.md).
