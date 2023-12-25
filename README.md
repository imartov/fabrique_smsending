# FABRIQUE_SMSENDING

## Overview

The goal of this project is to provide users with the ability to manage SMS mailings to their clients, including instant sending and scheduling.
The project faces the following tasks:
- creating, viewing, changing and deleting SMS newsletters
- creating, changing, deleting recipients of SMS messages - clients.

Key features of the project:
- asynchronization of sending and scheduling SMS mailings, which contributes to the fast and uninterrupted operation of the web server
- mailing lists and clients have filters (operator code, tag), which allows flexible management of clients;
- taking into account the time zone of clients

## Technologies Used

The project uses the following key technologies:
- Django
- Django Rest Framework (DRF)
- PostgreSQL
- Celery
- Celery Flower
- Docker Redis

## Project Structure

The project was developed on the Django framework and the Django rest framework and has the following classic structure:
```
fabrique_sms_sending/
│
├── config/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── .env
│   ├── asgi.py
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── smsending/
│   ├── __pycache__/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── service.py
│   ├── tasks.py
│   ├── test.py
│   ├── urls.py
│   └── views.py
│
├── manage.py
├── README.md
└── requirements.txt
```

## Installation

To install the project locally, you must complete the following steps:

```bash
# Clone the repository
git clone https://github.com/imartov/fabrique_smsending.git

# Navigate to the project directory
cd fabrique_smsending

# Install dependencies
pip install -r requirements.txt

# Create and apply migrations
python manage.py makemigrations
python manage.py migrate
```

## Settings

After installing the project, you need to perform the following settings (not necessary):

### Creating superuser
```bash
# Create a superuser (if applicable)
python manage.py createsuperuser
```

### Set environment variables

The project uses django-environ and the project modules have appropriate references to environment variables, so you need to:
1. Create `.env` file in the location specified in Project Structure
2. Define the following variables in `.env` file:
```env
DEFAULT_FROM_EMAIL=your_value
EMAIL_HOST_USER=your_value
EMAIL_HOST_PASSWORD=your_value
DATABASE_NAME=your_value
DATABASE_USER=your_value
DATABASE_PASSWORD=your_value
```

## Get started

To get started after installing and settings the project, you must run the following commands:

```bash
# Pull and run docker image of Redis for Celery broker 
docker run -d -p 6379:6379 redis

# Run Django web-server
python manage.py runserver

# Start Celery worker
celery -A config worker -l INFO -P eventlet

# Start Celery flower for monitoring
celery -A config flower
```

Visual task monitoring using Celery Flower will be available at the following address:
http://localhost:5555

## API Documentation

You can use the API documentation in <b>OpenAPI</b> format <a href="https://app.swaggerhub.com/apis/ALEXANDRKOSYREW/fabrique_smsending/2#/">here</a>.

### Endpoints

#### Create a client | <b>`POST /client/create/`</b>

**Description**: Create object of Client model

```bash
curl -X POST "http://127.0.0.1:8000/client/create/" -H "Content-Type: application/json" -d '{
    "phone_number": "7XXXXXXXXXX",
    "phone_code": 0,
    "tag": "any_tag",
    "timezone": "any_timezone"
}'
```
**Response:**
```json
{
    "phone_number": "7XXXXXXXXXX",
    "phone_code": 0,
    "tag": "any_tag",
    "timezone": "any_timezone"
}
```

#### Update a client | <b>`PUT /client/update/${clientId}/`</b>

**Description**: Update object of Client model

```bash
curl -X PUT "http://127.0.0.1:8000/client/update/${clientId}/" -H "Content-Type: application/json" -d '{
    "phone_number": "7XXXXXXXXXX",
    "phone_code": 1,
    "tag": "any_tag_updated",
    "timezone": "any_timezone_updated"
}'
```
**Response:**
```json
{
    "phone_number": "7XXXXXXXXXX",
    "phone_code": 1,
    "tag": "any_tag_updated",
    "timezone": "any_timezone_updated"
}
```

#### Delete a client | <b>`DELETE /client/delete/${clientId}/`</b>

**Description**: Delete object of Client model

```bash
curl -X DELETE "http://127.0.0.1:8000/client/delete/${clientId}/"
```
**Response:** `204 No Content`

#### Get sendings | <b>`GET /sending/get/`</b>

**Description**: Get all objects (list) of Sending model and general statistics on created mailings and the number of messages sent on them, grouped by status

```bash
curl -X GET "http://127.0.0.1:8000/sending/get/"
```
**Response:**
```json
[
    {
        "id": 1,
        "datetime_run": "2023-12-16T17:12:00Z",
        "message": "test sending",
        "phone_code_filter": 925,
        "tag_filter": "test",
        "datetime_finish": "2023-12-17T18:00:00Z",
        "messages": {
            "count": 6,
            "status_detail": [
                {
                    "status_send": 200,
                    "count": 3
                },
                {
                    "status_send": 401,
                    "count": 2
                },
                {
                    "status_send": 402,
                    "count": 1
                }
            ]
        }
    },
    {
        "id": 2,
        "datetime_run": "2023-12-14T21:55:00Z",
        "message": "message 2",
        "phone_code_filter": 102,
        "tag_filter": "test",
        "datetime_finish": "2023-12-08T09:52:00Z",
        "messages": {
            "count": 6,
            "status_detail": [
                {
                    "status_send": 200,
                    "count": 3
                },
                {
                    "status_send": 401,
                    "count": 2
                },
                {
                    "status_send": 402,
                    "count": 1
                }
            ]
        }
    },
    ...
]
```

#### Get a sending | <b>`GET /sending/detail/{sendingId}/`</b>

**Description**: Get object of Sending model and detailed statistics of sent messages for a specific object

```bash
curl -X GET "http://127.0.0.1:8000/sending/detail/${sendingId}/"
```
**Response:**
```json
{
    "id": 1,
    "datetime_run": "2023-12-16T17:12:00Z",
    "message": "test sending",
    "phone_code_filter": 925,
    "tag_filter": "test",
    "datetime_finish": "2023-12-17T18:00:00Z",
    "messages": {
        "count": 6,
        "messages": [
            {
                "datetime_send": "2023-12-13T23:25:00Z",
                "status_send": 200,
                "client": 4
            },
            {
                "datetime_send": "2023-12-23T04:32:00Z",
                "status_send": 402,
                "client": 4
            },
            {
                "datetime_send": "2023-12-15T18:16:00Z",
                "status_send": 200,
                "client": null
            },
            {
                "datetime_send": "2023-12-12T17:07:00Z",
                "status_send": 200,
                "client": null
            },
            {
                "datetime_send": "2023-12-14T23:16:00Z",
                "status_send": 401,
                "client": null
            },
            {
                "datetime_send": "2023-12-10T01:07:00Z",
                "status_send": 401,
                "client": null
            }
        ]
    }
}
```

#### Create a sending | <b>`POST /sending/create/`</b>

**Description**: Create an object of Sending model

```bash
curl -X POST "http://127.0.0.1:8000/sending/create/" -H "Content-Type: application/json" -d '{
  "datetime_run": "YYYY-MM-DDTHH:MM:SS.ffffffZ",
  "message": "any_text",
  "phone_code_filter": 0,
  "tag_filter": "any_tag",
  "datetime_finish": "YYYY-MM-DDTHH:MM:SS.ffffffZ"
}'
```
**Response:**
```json
{
    "datetime_run": "YYYY-MM-DDTHH:MM:SS.ffffffZ",
    "message": "any_text",
    "phone_code_filter": 0,
    "tag_filter": "any_tag",
    "datetime_finish": "YYYY-MM-DDTHH:MM:SS.ffffffZ"
}
```

#### Update a sending | <b>`PUT /sending/update/{sendingId}/`</b>

**Description**: Update an object of Sending model

```bash
curl -X PUT "http://127.0.0.1:8000/sending/create/${sendingId}/" -H "Content-Type: application/json" -d '{
  "datetime_run": "YYYY-MM-DDTHH:MM:SS.ffffffZ",
  "message": "any_text",
  "phone_code_filter": 0,
  "tag_filter": "any_tag",
  "datetime_finish": "YYYY-MM-DDTHH:MM:SS.ffffffZ"
}'
```
**Response:**
```json
{
    "datetime_run": "YYYY-MM-DDTHH:MM:SS.ffffffZ",
    "message": "any_text",
    "phone_code_filter": 0,
    "tag_filter": "any_tag",
    "datetime_finish": "YYYY-MM-DDTHH:MM:SS.ffffffZ"
}
```

#### Delete a sending | <b>`DELETE /sending/delete/{sendingId}/`</b>

**Description**: Delete an object of Sending model

```bash
curl -X DELETE "http://127.0.0.1:8000/sending/delete/${sendingId}/"
```
**Response:** `204 No Content`


## Models

The project complies with Django standards and has the following models.

### Sending

**Fields:**

- `id` (integer): The unique identifier for the item.
- `datetime_run` (datetime): Sending launch date and time in the ISO 8601 format. For example: "YYYY-MM-DDTHH:MM:SS.ssssssZ"
- `message` (string): Message text to be delivered to the client
- `phone_code_filter` (integer): Client properties filter - mobile operator code
- `tag_filter` (string): Client properties filter - tag
- `datetime_finish` (datetime): Sending end date and time in the ISO 8601 format. For example: "YYYY-MM-DDTHH:MM:SS.ssssssZ"

### Client

**Fields:**

- `id` (integer): The unique identifier for the item.
- `phone_number` (string): Client phone number in the format 7XXXXXXXXXX (X is a number from 0 to 9)
- `phone_code` (integer): Mobile operator code
- `tag` (string): Tag (arbitrary label)
- `timezone` (integer): Timezone. For example "Europe/Moscow"

### Message

**Fields:**

- `id` (integer): The unique identifier for the item.
- `datetime_send` (datetime): date and time of creation (sending) in the ISO 8601 format. For example: "YYYY-MM-DDTHH:MM:SS.ssssssZ"
- `status_send` (integer): Sending status
- `sms_sending` (integer): Id of the Sending object within which the message was sent
- `client` (integer): Id of the Client object to whom it was sent




## Contributing

You can contribute to this project.
Just contact the developer: alexandr.kosyrew@mail.ru

## License

This project is distributed publicly and has a royalty-free open non-exclusive license. The project is available for use for both private and commercial development.