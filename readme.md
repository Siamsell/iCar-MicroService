# 🚗 iCar Algeria — Microservices Car Platform

## Quick Start

```bash
gh repo clone OussamaBerredjem/icar-platform
cd icar-algerie-backend
cp .env.example .env
docker compose up --build -d
```

---

## Overview

iCar Algeria is a microservices-based car marketplace backend built with Django REST Framework. Three independent services communicate asynchronously through RabbitMQ, with Consul handling service health monitoring and Traefik acting as the API gateway and load balancer.

---

## Architecture

![diagram](https://enchere-dz.com/diagram.png)

---

## Services

| Service | Instances | Internal Port | Description |
|---|---|---|---|
| Auth | auth1, auth2 | 7860 | JWT authentication & user management |
| Catalog | car1, car2 | 7860 | Car listings & categories |
| Notification | notification1, notification2 | 7860 | User notifications |

Each service runs **2 instances** for redundancy and load balancing.

---

## How It Works

### Gateway (Traefik)
Traefik is the single entry point for all client requests. It reads healthy instances from Consul and automatically load balances traffic between them. If an instance goes down, Consul marks it unhealthy and Traefik stops routing to it within 30 seconds.

![traefik](https://enchere-dz.com/aos/traefik1.png)

### Service Discovery (Consul)
Each service instance registers itself in Consul with a shared service name (e.g. both `auth1` and `auth2` register as `auth`). Consul runs health checks every 30 seconds. Only passing instances are served to Traefik.

 ![rabbit](https://enchere-dz.com/aos/consul1.png)

### Messaging (RabbitMQ)
Services communicate asynchronously via RabbitMQ:
- **Auth** publishes user events (e.g. user created, user updated)
- **Catalog consumer** listens and syncs user data
- **Notification consumer** listens and sends notifications

  ![rabbit](https://enchere-dz.com/aos/rabbitmq.png)

This decouples services — no direct HTTP calls between them.

### Databases
Each service has its own isolated MySQL database:
- `auth-db` → Auth Service
- `car-db` → Catalog Service
- `notification-db` → Notification Service

---

## Local Access

### Via Gateway (load balanced)
| Route | URL |
|---|---|
| Auth Service | http://localhost/auth/ |
| Catalog Service | http://localhost/catalog/ |
| Notification Service | http://localhost/notifications/ |

### Direct Instance Access
| Instance | URL |
|---|---|
| auth1 | http://localhost:8001 |
| auth2 | http://localhost:8002 |
| car1 | http://localhost:8003 |
| car2 | http://localhost:8004 |
| notification1 | http://localhost:8005 |
| notification2 | http://localhost:8006 |

### Infrastructure UIs
| Tool | URL | Credentials |
|---|---|---|
| Traefik Dashboard | http://localhost:8080 | — |
| Consul UI | http://localhost:8500 | — |
| RabbitMQ UI | http://localhost:15672 | guest / guest |

---

## Setup After Start

Run migrations:
```bash
docker compose exec auth1 python manage.py migrate
docker compose exec car1 python manage.py migrate
docker compose exec notification1 python manage.py migrate
```

Create admin user:
```bash
docker compose exec auth1 python manage.py createsuperuser
```

---

## Environment Variables

Copy `.env.example` to `.env` and adjust:

```env
MYSQL_ROOT_PASSWORD=rootpassword
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
SECRET_KEY=your-secret-key
DEBUG=True
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.x, Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | MySQL 8.0 |
| Message Broker | RabbitMQ 3 |
| API Gateway | Traefik v3 |
| Service Discovery | Consul v1.15 |
| Containers | Docker, Docker Compose |
