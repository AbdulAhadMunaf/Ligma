# Ligma

This repository is a Django backend template that provides a solid foundation for building Django REST APIs. It includes common configurations, utilities, and best practices to help you get started quickly. Follow these steps to set up and run the application in a development environment.

## Prerequisites

Make sure you have the following installed:

- **Python 3.11+**
- **Docker & Docker Compose**

## Getting Started

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Backend-Template
```

### 2. Install Dependencies

Set up and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

configure pre-commit (you must have git)

```bash
$ pre-commit install
```

Then, install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the .env.example file to .env

```bash
cp .env.example .env
```

Open the .env file and configure your environment variables as needed.

### 4. Start PostgreSQL Database with Docker Compose

To run a PostgreSQL database in Docker, use the provided docker-compose.dev.yml file:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This will set up the PostgreSQL container with the following connection details:
` PostgreSQL URL: postgresql://admin:admin@localhost:5432/backend_db`

Make sure these credentials match the settings in your `.env` file. You can customize the database name and credentials in the `docker-compose.dev.yml` file.

### 5. Run Database Migrations

Apply the database migrations to set up the database schema:

```bash
python manage.py migrate
```

### 6. Collect Static Files

Run the following command to collect static files:

```bash
python manage.py collectstatic
```

### 7. Run the Application

Finally, start the Django development server:

```bash
python manage.py runserver
```

Your application will be available at http://127.0.0.1:8000/.

## Creating New Apps

To create a new Django app using the project template:

```bash
python manage.py startapp {app_name} --template conf/app_template
```

After creating the app, move it to the `apps` folder to maintain the project structure.

## Access Control: Roles (Groups) and Permissions

The `access_required` decorator is a utility for enforcing access control in Django views based on user group membership and permissions. This section explains how to use the decorator in your project.

### Usage

The `access_required` decorator ensures that only users who belong to specific groups and/or have specific permissions can access a particular view.

#### Parameters

- `groups` (required): A single group name (string) or a list of group names the user must belong to. For consistency, use `UserGroupChoices` (e.g., `UserGroupChoices.admin.value`).
- `permissions` (optional): A single permission (string) or a list of permissions the user must have. For consistency, use `UserPermissionChoices` (e.g., `UserPermissionChoices.CAN_VIEW_REPORTS.value`).

## How to Use

First, ensure you import the decorator and choices enums from your project:

```python
from apps.users.choices import UserGroupChoices, UserPermissionChoices
from utils.permissions import access_required
```

### Basic Example: Enforcing Group Membership

```python
@access_required(groups=[UserGroupChoices.admin.value])
def some_view(self, request, *args, **kwargs):
    # Your view logic here
    return HttpResponse("Welcome, Admin!")
```

- In this example, only users belonging to the Admin group can access the view.
- If the user does not belong to the Admin group, they will receive a PermissionDenied error.

### Example: Enforcing Group Membership and Permissions

```python
@access_required(
    groups=[UserGroupChoices.admin.value],
    permissions=[UserPermissionChoices.CAN_CHANGE_PRODUCT_INFO.value]
)
def some_view(self, request, *args, **kwargs):
    # Your view logic here
    return HttpResponse("Welcome, Admin with permission to change product info!")
```

- The user must belong to the Admin group and have the `CAN_CHANGE_PRODUCT_INFO` permission.

### Example: Allow Superuser Bypass

```python
@access_required(
    superuser_allowed=True
)
def secure_view(request):
    return HttpResponse("Access granted to Admin or Superuser.")
```

### Example: No Restrictions (Superuser Only)

```python
@access_required()
def secure_view(request):
    return HttpResponse("Access granted to Admin or Superuser.")
```

## Error Handling

If a user does not meet the required conditions:

- Group Check: If the user does not belong to any specified group, a PermissionDenied exception is raised.
- Permission Check: If permissions are specified and the user does not have any of the required permissions, a PermissionDenied exception is raised.

## Collaboration Backend (LIGMA)

This repository now includes a room-based collaboration backend with event sourcing, node-level RBAC, replay support, and text conflict handling.

### Implemented Components

- Room model + membership roles (`owner`, `editor`, `viewer`)
- Append-only immutable room event stream
- Snapshot projection for fast scene hydration
- Node-level ACL (`node_id -> allowed_roles`)
- Delta mutation processing (`operations` contract)
- Replay endpoint for reconnect (`after_sequence`)
- Text patch conflict handling with deterministic tie-break
- Centrifugo integration points for realtime publish/subscribe

Core app path: `apps/collaboration/`

### Data Model Summary

- `CollaborationRoom`: room metadata and `last_event_sequence`
- `CollaborationRoomMember`: per-user room role
- `CollaborationRoomEvent`: immutable event stream (`sequence`, payload, actor, timestamp)
- `CollaborationRoomSnapshot`: current projected scene (`elements`, `appState`, `files`, `libraryItems`)
- `CollaborationNodeAccess`: node-level lock policy (`node_id`, `allowed_roles`)
- `CollaborationTextOperation`: applied text ops (`base_version`, `applied_version`, `client_id`, `client_sequence`)

### API Endpoints

Base path: `/api/collaboration/`

`POST /rooms/`: create room

`GET /rooms/`: list rooms for current user

`GET /rooms/<room_uuid>/`: room details

`GET /rooms/<room_uuid>/scene/`: hydration payload for Excalidraw

`POST /rooms/<room_uuid>/members/`: add/update member role (owner only)

`GET /rooms/<room_uuid>/members/`: list members

`POST /rooms/<room_uuid>/node-access/`: set per-node ACL (owner only)

`GET /rooms/<room_uuid>/node-access/`: list node ACL entries

`POST /rooms/<room_uuid>/events/`: append event (scene or deltas)

`GET /rooms/<room_uuid>/events/?after_sequence=<n>&limit=<n>`: list events

`GET /rooms/<room_uuid>/replay/?after_sequence=<n>&limit=<n>`: replay missed events

`POST /rooms/<room_uuid>/realtime-token/`: connection/subscription tokens

`POST /centrifugo/publish/`: publish proxy endpoint used by Centrifugo

### Event-Sourcing Contract

All canvas mutations are stored as immutable events. Current state is a projection (`CollaborationRoomSnapshot`) derived from the event stream.

Two accepted payload shapes:

1. Scene snapshot shape

```json
{
  "payload": {
    "elements": [],
    "appState": {},
    "files": {},
    "libraryItems": []
  }
}
```

2. Delta operations shape

```json
{
  "payload": {
    "metadata": {
      "client_id": "tab-a",
      "client_sequence_start": 100
    },
    "operations": [
      {
        "op": "element.create",
        "element": {"id": "node-1", "type": "rectangle", "x": 0, "y": 0}
      },
      {
        "op": "text.patch",
        "node_id": "text-2",
        "text_delta": {
          "position": 4,
          "delete_count": 0,
          "insert_text": "X",
          "base_version": 12
        }
      }
    ]
  }
}
```

Supported `op` values:

- `element.create`
- `element.update`
- `element.delete`
- `text.patch`
- `node_acl.set`
- `app_state.update`
- `files.update`

### Node-Level RBAC

Node lock policy is stored in `CollaborationNodeAccess`.

- If node has no ACL entry: room-level edit permission applies.
- If node has ACL entry: actor role must be in `allowed_roles`.
- `node_acl.set` can only be performed by room `owner`.
- Enforcement is server-side during mutation validation.

### Text Conflict Handling

Text patches use:

- `text_delta.base_version`
- `text_delta.position`
- `text_delta.delete_count`
- `text_delta.insert_text`
- `text_delta.client_id`
- `text_delta.client_sequence`

Behavior:

- Incoming `text.patch` is rebased over already-applied operations with higher version.
- Tie-break for same-position inserts is deterministic by `(client_id, client_sequence)`, not arrival order.
- Duplicate retransmits are idempotent via unique key `(room, node_id, client_id, client_sequence)`.
- If `client_id` or `client_sequence` is missing on an op, backend can infer from payload metadata (`client_id`, `client_sequence_start` or `client_sequence`).

### Reconnect & Replay

Clients should store last acknowledged event sequence and request:

`GET /rooms/<room_uuid>/replay/?after_sequence=<last_seen>`

Response:

- `events`: missed events only
- `from_sequence`: requested base
- `to_sequence`: current room head
- `has_more`: whether additional replay calls are needed

### Centrifugo Config Variables

Required backend settings:

- `CENTRIFUGO_HMAC_SECRET`
- `CENTRIFUGO_HTTP_API_KEY`
- `CENTRIFUGO_API_URL`
- `CENTRIFUGO_TOKEN_TTL_SECONDS`
- `CENTRIFUGO_HTTP_TIMEOUT_SECONDS`

### Test Commands

```bash
pytest -vv apps/collaboration/tests/test_room_api.py
pytest -vv apps/collaboration/tests/test_room_members_api.py
pytest -vv apps/collaboration/tests/test_room_events_api.py
```

### Current Scope Note

Current text conflict support is an OT-style deterministic rebase baseline for same-node text operations. It is not yet a full CRDT implementation.
