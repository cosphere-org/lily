
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
                "is_private": true
            },
            "examples": {
                "some": "examples"
            },
            "meta": {
                "@type": "meta",
                "description": "Debitis rem ex consequatur fugit ullam natus labore.",
                "domain": {
                    "@type": "domain",
                    "id": "eos",
                    "name": "domain"
                },
                "title": "Occaecati provident deserunt quibusdam id ab expedita quia."
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
    "enums": [],
    "name": "test",
    "version_info": {
        "@type": "version_info",
        "available": [],
        "deployed": "2.5.6",
        "displayed": "2.5.6"
    }
}
```
