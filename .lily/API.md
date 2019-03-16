
# CoSphere API
CoSphere's API with hypermedia links
## Docs Management
### READ_ENTRY_POINT: GET /
Read Entry Point 
Serve Service Entry Point data: - current version of the service - list of all available commands together with their configurations - examples collected for a given service.
#### 200 (ENTRY_POINT_READ)
Request:
```http
GET /?with_schemas=False HTTP/1.1
X-CS-ACCOUNT-TYPE: ADMIN
X-CS-USER-ID: 190
```
Respone:
```json
{
    "@event": "ENTRY_POINT_READ",
    "@type": "entrypoint",
    "commands": {
        "UPDATE_HELLO": {
            "@type": "command",
            "access": {
                "@type": "access",
                "access_list": [
                    "ANY"
                ],
                "is_external": false,
                "is_private": true
            },
            "meta": {
                "@type": "meta",
                "description": "Debitis voluptatem iure aliquam alias.",
                "domain": {
                    "@type": "domain",
                    "id": "labore",
                    "name": "domain"
                },
                "title": "Qui exercitationem voluptatem facere."
            },
            "method": "PUT",
            "path_conf": {
                "path": "conf"
            },
            "source": {
                "@type": "source",
                "end_line": 15,
                "filepath": "/tests/__init__.py",
                "start_line": 14
            }
        }
    },
    "name": "test",
    "version": "2.5.6"
}
```
#### 500 (GENERIC_ERROR_OCCURRED)
Request:
```http
GET /?is_private=False HTTP/1.1
X-CS-ACCOUNT-TYPE: ADMIN
X-CS-USER-ID: 190
```
Respone:
```json
{
    "@event": "GENERIC_ERROR_OCCURRED",
    "@type": "error",
    "errors": [
        "'examples'"
    ]
}
```
