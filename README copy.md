
# Django Backend Template

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
