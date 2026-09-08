# Verification Codes API

Base URL: `{APP_URL}/api` (e.g. `http://localhost/vocabadmin/public/api`)

Both endpoints are rate-limited by the `throttle:api` middleware.

## 1. Generate a code (admin/backend use only)

Registers a phone number as an activation code in the `verification` table.

**Endpoint:** `POST /generate`

**Headers:**
| Header | Required | Value |
|---|---|---|
| `X-API-KEY` | Yes | Must match `VERIFICATION_GENERATE_KEY` in `.env` |
| `Content-Type` | Yes | `application/json` |
| `Accept` | Yes | `application/json` |

**Body:**
```json
{
    "phone_number": "+15551234567"
}
```

**Success response — `201 Created`:**
```json
{
    "success": true,
    "code": "+15551234567"
}
```

**Unauthorized — `401 Unauthorized`** (missing/invalid `X-API-KEY`):
```json
{
    "success": false,
    "message": "Unauthorized."
}
```

**Validation error — `422 Unprocessable Content`** (missing/duplicate `phone_number`):
```json
{
    "message": "The phone number has already been taken.",
    "errors": {
        "phone_number": ["The phone number has already been taken."]
    }
}
```

**curl example:**
```bash
curl -X POST http://localhost/vocabadmin/public/api/generate \
  -H "X-API-KEY: <VERIFICATION_GENERATE_KEY>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"phone_number": "+15551234567"}'
```

## 2. Verify / activate a code (client app use)

Activates a code for a device, or confirms it's already active on that device.

**Endpoint:** `POST /verify`

**Headers:**
| Header | Required | Value |
|---|---|---|
| `Content-Type` | Yes | `application/json` |
| `Accept` | Yes | `application/json` |

**Body:**
```json
{
    "code": "+15551234567",
    "device_id": "device-unique-id"
}
```

**Responses:**
| Status | Condition | Body |
|---|---|---|
| `200` | First activation | `{"success": true, "message": "Activation successful."}` |
| `200` | Already active on same device | `{"success": true, "message": "Already activated on this device."}` |
| `403` | Active on a different device | `{"success": false, "message": "This code is already used on another device."}` |
| `404` | Code not found | `{"success": false, "message": "Invalid activation code."}` |

**curl example:**
```bash
curl -X POST http://localhost/vocabadmin/public/api/verify \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"code": "+15551234567", "device_id": "device-unique-id"}'
```

## 3. Get video links

Returns all video links created in the admin panel, ordered by their configured position.

**Endpoint:** `GET /videos`

**Headers:**
| Header | Required | Value |
|---|---|---|
| `Accept` | Recommended | `application/json` |

**Success response - `200 OK`:**
```json
{
        "success": true,
        "videos": [
                {
                        "id": 1,
                        "title": "Common English Phrases",
                        "url": "https://www.youtube.com/watch?v=example",
                        "position": 1
                }
        ]
}
```

`title` may be `null`. An empty list is returned when no video links are available.

**curl example:**
```bash
curl -X GET http://localhost/vocabadmin/public/api/videos \
    -H "Accept: application/json"
```

## 4. Get audio links

Returns all audio links created in the admin panel, ordered by their configured position.

**Endpoint:** `GET /audios`

**Headers:**
| Header | Required | Value |
|---|---|---|
| `Accept` | Recommended | `application/json` |

**Success response - `200 OK`:**
```json
{
        "success": true,
        "audios": [
                {
                        "id": 2,
                        "title": "Daily Listening Practice",
                        "url": "https://www.youtube.com/watch?v=example",
                        "position": 1
                }
        ]
}
```

`title` may be `null`. An empty list is returned when no audio links are available.

**curl example:**
```bash
curl -X GET http://localhost/vocabadmin/public/api/audios \
    -H "Accept: application/json"
```

## Configuration

- `VERIFICATION_GENERATE_KEY` in [.env](../.env) — secret key required to call `/generate`. Keep it private, only share with trusted backend systems.
- Relevant files:
  - [routes/api.php](../routes/api.php)
  - [app/Http/Controllers/Api/VerifyController.php](../app/Http/Controllers/Api/VerifyController.php)
    - [app/Http/Controllers/Api/MediaController.php](../app/Http/Controllers/Api/MediaController.php)
  - [app/Models/Verification.php](../app/Models/Verification.php)
    - [app/Models/MediaLink.php](../app/Models/MediaLink.php)
  - [config/services.php](../config/services.php)
