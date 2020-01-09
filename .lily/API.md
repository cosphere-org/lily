
# CoSphere API
CoSphere's API with hypermedia links
## Docs Management
### READ_ENTRY_POINT: GET /
Read Entry Point 
Serve Service Entry Point data: - current or chosen version of the service - list of all available commands together with their configurations - examples collected for a given service.
#### 200 (ENTRY_POINT_READ)
Request:
```http
GET /?domain_id=PATHS HTTP/1.1
X-CS-ACCOUNT-TYPE: ADMIN
X-CS-USER-ID: 190
```
Respone:
```json
{
    "@enums": [
        {
            "A": "X"
        }
    ],
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
                "description": "Amet incidunt sint deleniti perspiciatis.",
                "domain": {
                    "@type": "domain",
                    "id": "paths",
                    "name": "domain"
                },
                "title": "Temporibus provident voluptatum atque tenetur similique corrupti."
            },
            "method": "POST",
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
        },
        "DELETE_HELLO": {
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
                "description": "Aliquid minus assumenda atque doloribus.",
                "domain": {
                    "@type": "domain",
                    "id": "paths",
                    "name": "domain"
                },
                "title": "Aperiam magni exercitationem saepe eveniet ullam."
            },
            "method": "PUT",
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
