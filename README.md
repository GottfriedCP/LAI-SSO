This web API with token-based auth is made for serving clients on various front-ends: mobile app (React Native) and web app, primarily using JSON message format.

## Base URL

-redacted-

## API Versioning

This API is made using Django Rest Framework; an API version is actually an app with name format `apivX`, e.g., `apiv1` for version one.

## Database

Our DBMS is MariaDB.

## Entities and Their Relation

-redacted-

## Endpoints

To specify message format used on request and response body, a special suffix must be appended, e.g., for JSON: `https://the_server_address/api/1/login.json`. In general consists of:

1.  User
2.  Device
3.  Data Item
