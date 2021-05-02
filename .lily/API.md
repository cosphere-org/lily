
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
                "is_private": true
            },
            "examples": {
                "some": "examples"
            },
            "meta": {
                "@type": "meta",
                "description": "In eveniet repellendus iste quo earum dolores.",
                "domain": {
                    "@type": "domain",
                    "id": "paths",
                    "name": "domain"
                },
                "title": "Illo error vel optio deserunt."
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
                "is_private": true
            },
            "examples": {
                "some": "examples"
            },
            "meta": {
                "@type": "meta",
                "description": "Modi ab deserunt enim praesentium laboriosam veniam provident dolores.",
                "domain": {
                    "@type": "domain",
                    "id": "paths",
                    "name": "domain"
                },
                "title": "Reprehenderit laudantium in architecto cum sapiente quasi adipisci."
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
        }
    },
    "enums": [
        {
            "A": "X"
        }
    ],
    "name": "test",
    "version_info": {
        "@type": "version_info",
        "available": [],
        "deployed": "2.5.6",
        "displayed": "2.5.6"
    }
}
```
