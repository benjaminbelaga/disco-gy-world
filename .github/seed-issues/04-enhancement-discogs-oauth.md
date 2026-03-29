# Discogs OAuth app registration for collection sync

**Labels:** enhancement, feature, backend

## Description

To enable the "Connect your Discogs collection" feature, we need to implement Discogs OAuth 1.0a authentication.

## Requirements

- Register a Discogs OAuth consumer application
- Implement the 3-leg OAuth flow in the FastAPI backend
- Fetch user collection (paginated, 100 items/page, 60 req/min rate limit)
- Match collection releases to DiscoWorld coordinates
- Store user-collection mapping for returning visits

## Technical Notes

- Discogs uses OAuth 1.0a (not 2.0)
- Rate limit: 60 authenticated requests per minute
- Collection endpoint: `GET /users/{username}/collection/folders/0/releases`
- A 5,000 record collection takes ~1 minute to fully import

## References
- [Discogs Auth Flow](https://www.discogs.com/developers/#page:authentication)
- [Discogs Collection API](https://www.discogs.com/developers/#page:user-collection)
