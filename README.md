<h1 align="center">🛒 Marketplace — Multi-Vendor E-commerce API</h1>

<p align="center">
  A production-style REST API for a multi-vendor marketplace: buyers browse and order products, sellers manage their own catalog and orders, all behind JWT auth, throttling and a Dockerized PostgreSQL + Nginx + Gunicorn stack.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Django_5.2-092E20?style=flat-square&logo=django&logoColor=white" alt="Django"/>
  <img src="https://img.shields.io/badge/DRF_3.16-A30000?style=flat-square&logo=django&logoColor=white" alt="DRF"/>
  <img src="https://img.shields.io/badge/PostgreSQL_17-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white" alt="Nginx"/>
  <img src="https://img.shields.io/badge/Gunicorn-499848?style=flat-square&logo=gunicorn&logoColor=white" alt="Gunicorn"/>
</p>

---

## 📖 Overview

**Marketplace** is the backend for an online store with **two roles** — **buyer** and **seller**:

- A **buyer** browses categories and products, manages a cart, saves shipping addresses, places orders (checkout) and leaves product reviews.
- A **buyer can apply to become a seller**; after approval (`is_approved`) the seller gets a business profile and can create / update / delete products and track orders for their items.
- Everything is exposed as a versioned, throttled REST API and fully documented with **Swagger UI** (`drf-spectacular`).

The codebase is organized around a shared `common` app (base models, managers, permissions, pagination, utilities), which keeps the domain apps small and consistent.

---

## ✨ Highlights

- 🔐 **JWT auth** (SimpleJWT) with **refresh-token rotation + blacklisting**; custom **email-based** user model (`AbstractBaseUser`).
- 👥 **Role-based access** via custom permissions: `IsOwner`, `IsSeller` (checks `account_type` **and** `is_approved`), `IsStaff`.
- 🧱 **Reusable base layer** (`common` app):
  - `BaseModel` — UUID primary key + `created_at` / `updated_at`.
  - `IsDeletedModel` — **soft delete** (`is_deleted` / `deleted_at`) with `delete()` / `hard_delete()`.
  - `GetOrNoneManager` — clean `get_or_none()` lookups instead of try/except everywhere.
- 🔎 **PostgreSQL trigram search** (`TrigramSimilarity`) for fuzzy product-name search, plus price / stock filters via `django-filter`.
- 📦 **Cart → Checkout → Order** flow with `tx_ref` transaction references and delivery/payment status enums.
- ⚡ **Query optimization** with `select_related` / `prefetch_related` on hot list endpoints.
- 🚦 **Rate limiting** (throttling): `50/min` anon, `100/min` authenticated, plus a scoped throttle.
- 🔢 **API versioning** via query parameter (custom `QueryParameterVersioning`).
- 📄 **Custom pagination** with rich metadata (`total_count`, `page_number`, `total_pages`).
- 🧾 **Auto-generated OpenAPI docs** with per-endpoint summaries, descriptions and tags.
- 🐳 **Dockerized**: Gunicorn app + PostgreSQL (with healthcheck) + Nginx reverse proxy serving static/media.

---

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.12 |
| Framework | Django 5.2 · Django REST Framework 3.16 |
| Auth | djangorestframework-simplejwt (rotation + blacklist) |
| Database | PostgreSQL 17 (psycopg 3) |
| Search | PostgreSQL `pg_trgm` (TrigramSimilarity) |
| API docs | drf-spectacular (OpenAPI 3 / Swagger UI) |
| Filtering | django-filter |
| Slugs / images | django-autoslug · Pillow |
| Server | Gunicorn (+ uvicorn / adrf available for async) |
| Reverse proxy | Nginx |
| Orchestration | Docker · docker-compose |
| Config | python-dotenv (`.env`) |

---

## 🧱 Project structure

```text
marketplace/
├── core/                  # settings, urls, wsgi/asgi
├── apps/
│   ├── common/            # BaseModel, IsDeletedModel, managers, permissions, pagination, utils
│   ├── accounts/          # custom email User, JWT auth, registration, API versioning
│   ├── profiles/          # profile, shipping addresses, buyer orders & order items
│   ├── sellers/           # seller onboarding, seller product CRUD, seller orders
│   ├── shop/              # categories, products, cart, checkout (+ trigram filter)
│   └── reviews/           # product reviews (1–5 rating, one per user/product)
├── nginx/                 # Nginx Dockerfile + reverse-proxy config
├── Dockerfile             # app image (python:3.12-alpine)
├── docker-compose.yml     # web + db + nginx
└── requirements.txt
```

---

## 🗃️ Data model (high level)

```text
User (email login, UUID, account_type: BUYER|SELLER, soft-delete)
 ├─ Seller (1—1)        business + bank info, is_approved
 ├─ ShippingAddress (N) delivery details
 ├─ Order (N)           tx_ref, delivery_status, payment_status, snapshot of address
 │   └─ OrderItem (N)   product + quantity  (cart item when order = NULL)
 └─ Review (N)          rating 1–5, unique per (user, product)

Category (slug) ─< Product (slug, 3 images, price_old/current, in_stock)
Product >─ Seller
```

---

## 🔌 API Endpoints

### Auth — `/auth/`
| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/auth/` | Register a new user |
| `POST` | `/auth/token/` | Obtain JWT pair |
| `POST` | `/auth/token/refresh/` | Refresh access token |
| `POST` | `/auth/token/verify/` | Verify token |
| `GET` | `/auth/version/` | Returns resolved API version |

### Profiles — `/profiles/`
| Method | Path | Description |
| --- | --- | --- |
| `GET/PUT/DELETE` | `/profiles/` | Get / update / deactivate own account |
| `GET/POST` | `/profiles/shipping_addresses/` | List / create shipping addresses |
| `GET/PUT/DELETE` | `/profiles/shipping_addresses/detail/<id>/` | Manage one address |
| `GET` | `/profiles/orders/` | My orders |
| `GET` | `/profiles/orders/<tx_ref>/` | Items of one order |

### Shop — `/shop/`
| Method | Path | Description |
| --- | --- | --- |
| `GET/POST` | `/shop/categories/` | List / create categories |
| `GET` | `/shop/categories/<slug>/` | Products in a category |
| `GET` | `/shop/sellers/<slug>/` | Products of a seller |
| `GET` | `/shop/products/` | All products (search, filter, paginate) |
| `GET` | `/shop/products/<slug>/` | Product detail |
| `GET/POST` | `/shop/cart/` | View cart / toggle cart item |
| `POST` | `/shop/checkout/` | Create an order from the cart |

### Sellers — `/sellers/`
| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/sellers/` | Apply to become a seller |
| `GET/POST` | `/sellers/products/` | List / create own products |
| `PUT/DELETE` | `/sellers/product/<slug>/` | Update / delete own product |
| `GET` | `/sellers/orders/` | Orders containing my products |
| `GET` | `/sellers/orders/<tx_ref>/` | Items of an order for my products |

### Reviews — `/review/`
| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/review/my/` | My reviews |
| `GET` | `/review/product/<slug>/` | Reviews of a product |
| `POST` | `/review/create/<slug>/` | Create a review |
| `GET/PUT/DELETE` | `/review/detail/<slug>/` | Get / update / delete my review |

### Docs
| Path | Description |
| --- | --- |
| `/api/schema/` | OpenAPI 3 schema |
| `/api/docs/` | Swagger UI |

> 💡 API version can be passed as a query parameter, e.g. `?version=2`.

---

## 🚀 Getting started

### Option A — Docker (recommended)

```bash
git clone https://github.com/Ula19/marketplace.git
cd marketplace

# create .env (see variables below), then:
docker compose up --build

# run migrations / create a superuser inside the web container
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

App is served through Nginx on **http://localhost** (and the app directly on `:8000`).

### Option B — Local

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# requires a running PostgreSQL and a .env
python manage.py migrate
python manage.py runserver
```

Then open:
- Swagger UI → `/api/docs/`
- Admin → `/admin/`

> ℹ️ Product fuzzy search uses the PostgreSQL `pg_trgm` extension — enable it once with `CREATE EXTENSION IF NOT EXISTS pg_trgm;`.

### Environment variables (`.env`)

| Variable | Description | Example |
| --- | --- | --- |
| `SECRET_KEY` | Django secret key | `change-me` |
| `SQL_DATABASE` | Database name | `marketplace_db` |
| `SQL_USER` | DB user | `postgres` |
| `SQL_PASSWORD` | DB password | `postgres` |
| `SQL_HOST` | DB host (`db` in docker-compose) | `db` |
| `SQL_PORT` | DB port | `5432` |

---

## 🧭 Roadmap / possible improvements

- [ ] Payment provider integration (currently order/payment statuses are modeled, not charged)
- [ ] Average product rating aggregation exposed on product detail
- [ ] Tests (`pytest` / DRF `APITestCase`) and CI pipeline
- [ ] Move `DEBUG` / `ALLOWED_HOSTS` fully to environment for production

---

<p align="center"><i>Built by <a href="https://github.com/Ula19">@Ula19</a> — backend developer.</i></p>
