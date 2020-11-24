
# CoSphere API
CoSphere's API with hypermedia links
## Docs Management
### READ_ENTRY_POINT: GET /
Read Entry Point 
Serve Service Entry Point data: - current or chosen version of the service - list of all available commands together with their configurations - examples collected for a given service.
#### 200 (ENTRY_POINT_READ)
Request:
```http
GET / HTTP/1.1
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
        "UPDATE_HELLO": {
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
                "description": "Impedit doloremque ullam at mollitia.",
                "domain": {
                    "@type": "domain",
                    "id": "nulla",
                    "name": "domain"
                },
                "title": "Mollitia dolore eveniet natus occaecati occaecati minima."
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
        "available": [
            "2.120.0",
            "2.14.5",
            "2.5.6",
            "1.0.0"
        ],
        "deployed": "2.5.6",
        "displayed": "2.5.6"
    }
}
```
