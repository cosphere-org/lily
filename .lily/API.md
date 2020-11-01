
# CoSphere API
CoSphere's API with hypermedia links
## Docs Management
### READ_ENTRY_POINT: GET /
Read Entry Point 
Serve Service Entry Point data: - current or chosen version of the service - list of all available commands together with their configurations - examples collected for a given service.
#### 200 (ENTRY_POINT_READ)
Request:
```http
GET /?is_private=False HTTP/1.1
X-CS-ACCOUNT-TYPE: ADMIN
X-CS-USER-ID: 190
```
Respone:
```json
{
    "@enums": [],
    "@event": "ENTRY_POINT_READ",
    "@type": "entrypoint",
    "commands": {
        "CREATE_HELLO": {
            "@type": "command",
            "access": {
                "@type": "access",
                "access_list": [
                    "ANY"
                ],
                "is_external": false,
                "is_private": false
            },
            "examples": {
                "some": "examples"
            },
            "meta": {
                "@type": "meta",
                "description": "Laudantium accusamus culpa aliquam enim ab explicabo delectus explicabo.",
                "domain": {
                    "@type": "domain",
                    "id": "nam",
                    "name": "domain"
                },
                "title": "Dolores voluptatibus vero qui itaque."
            },
            "method": "DELETE",
            "path_conf": {
                "path": "conf"
            },
            "schemas": {
                "some": "schemas"
            },
            "source": {
                "@type": "source",
                "end_line": 15,
                "filepath": "/tests/factory.py",
                "start_line": 14
            }
        }
    },
    "name": "test",
    "version_info": {
        "@type": "version_info",
        "available": [],
        "deployed": "2.5.6",
        "displayed": "2.5.6"
    }
}
```
