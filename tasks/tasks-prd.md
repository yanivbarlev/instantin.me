## Relevant Files

- `app/main.py` - FastAPI application entry point and configuration
- `app/models/` - Database models for users, products, orders, etc.
- `app/routers/` - API route handlers for different feature areas
- `app/services/` - Business logic services
- `app/templates/` - Jinja2 templates for storefront rendering
- `app/static/` - CSS, JavaScript, and static assets
- `app/auth/` - Authentication and authorization logic
- `app/payments/` - Stripe and PayPal integration services
- `app/ai/` - AI page builder and migration services
- `app/analytics/` - Analytics tracking and dashboard
- `app/tasks/` - Celery background tasks for raffles and payouts
- `app/utils/` - Utility functions and helpers
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Container orchestration for development
- `alembic/` - Database migration files
- `tests/` - Comprehensive test suite

### Notes

- This is a FastAPI application using PostgreSQL, deployed on PythonAnywhere
- Background tasks use Celery + Redis for raffle selection and payouts
- File storage uses AWS S3 for digital downloads and media
- AI services use Kimi k2 via Groq API and Unsplash API for images
- Payment processing via Stripe Connect and PayPal
- Mobile-first responsive design with Tailwind CSS

## Tasks

- [x] 1.0 Project Setup and Core Infrastructure
  - [x] 1.1 Create `requirements.txt` with specific versions: FastAPI 0.104.1, SQLAlchemy 2.0.23, Alembic 1.12.1, Celery 5.3.4, Redis 5.0.1, Stripe 7.8.0, boto3 1.34.0, Jinja2 3.1.2, python-multipart 0.0.6, python-jose[cryptography] 3.3.0, passlib[bcrypt] 1.7.4, python-dotenv 1.0.0, httpx 0.25.2, Pillow 10.1.0, authlib 1.2.1, beautifulsoup4 4.12.2
  - [x] 1.2 Create `.env.example` file with all required environment variables: DATABASE_URL, REDIS_URL, STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET, GROQ_API_KEY, UNSPLASH_API_KEY, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
  - [x] 1.3 Create `docker-compose.yml` with PostgreSQL 15, Redis 7, and app service configurations
  - [x] 1.4 Create `app/__init__.py` (empty file for Python package)
  - [x] 1.5 Create `app/main.py` with FastAPI app initialization, CORS middleware, and basic health check endpoint
  - [x] 1.6 Create `app/config.py` with Pydantic Settings class for environment variable management
  - [x] 1.7 Create `app/database.py` with SQLAlchemy engine, SessionLocal, and Base class setup
  - [x] 1.8 Create `alembic.ini` configuration file for database migrations
  - [x] 1.9 Initialize Alembic with `alembic init alembic` and configure `alembic/env.py` to use app models
  - [x] 1.10 Create `app/utils/__init__.py` and `app/utils/helpers.py` with common utility functions

- [x] 2.0 Authentication and User Management System
  - [x] 2.1 Create `app/models/user.py` with User SQLAlchemy model (id, email, hashed_password, is_verified, created_at, updated_at, stripe_account_id, paypal_email)
  - [x] 2.2 Create `app/schemas/user.py` with Pydantic models: UserCreate, UserResponse, UserLogin, TokenResponse
  - [x] 2.3 Create `app/auth/__init__.py` (empty file)
  - [x] 2.4 Create `app/auth/jwt.py` with JWT token creation, verification, and decode functions using python-jose
  - [x] 2.5 Create `app/auth/password.py` with password hashing and verification using passlib and bcrypt
  - [x] 2.6 Create `app/auth/dependencies.py` with get_current_user dependency for FastAPI route protection
  - [x] 2.7 Create `app/routers/auth.py` with endpoints: POST /register, POST /login, POST /verify-email, GET /me
  - [x] 2.8 Create `app/services/email.py` with email sending functionality for verification codes
  - [x] 2.9 Create `app/services/auth.py` with business logic for user registration, login, and verification
  - [x] 2.10 Add Google OAuth integration with `authlib` library in `app/auth/oauth.py`
  - [x] 2.11 Create database migration for users table using Alembic
  - [x] 2.12 Test authentication system with basic endpoints

- [x] 3.0 Database Models and Migrations
  - [x] 3.1 Create `app/models/__init__.py` with imports for all models
  - [x] 3.2 Create `app/models/storefront.py` with Storefront model (id, user_id, name, slug, theme, custom_css, is_published, created_at, updated_at)
  - [x] 3.3 Create `app/models/product.py` with Product model (id, storefront_id, name, description, price, product_type, file_url, inventory_count, is_active)
  - [x] 3.4 Create `app/models/order.py` with Order model (id, storefront_id, buyer_email, total_amount, status, stripe_payment_intent_id, created_at)
  - [x] 3.5 Create `app/models/order_item.py` with OrderItem model (id, order_id, product_id, quantity, price_at_time)
  - [x] 3.6 Create `app/models/drop.py` with Drop model (id, name, description, start_date, end_date, is_active, created_by_user_id)
  - [x] 3.7 Create `app/models/drop_participant.py` with DropParticipant model (id, drop_id, user_id, revenue_percentage)
  - [x] 3.8 Create `app/models/raffle.py` with Raffle model (id, month, year, total_prize_pool, status) and RaffleEntry model (id, raffle_id, user_id, ticket_count)
  - [x] 3.9 Create `app/models/analytics.py` with PageView model (id, storefront_id, visitor_ip, user_agent, created_at)
  - [x] 3.10 Create migration for all models: `alembic revision --autogenerate -m "create all tables"`
  - [x] 3.11 Update `app/database.py` to import all models for proper table creation

- [ ] 4.0 Storefront Creation Engine (Manual, AI, Migration)
  - [x] 4.1 Create `app/schemas/storefront.py` with StorefrontCreate, StorefrontUpdate, StorefrontResponse Pydantic models
  - [x] 4.2 Create `app/services/storefront.py` with CRUD operations for storefront management
  - [x] 4.3 Create `app/routers/storefront.py` with endpoints: POST /storefronts, GET /storefronts/{slug}, PUT /storefronts/{id}, DELETE /storefronts/{id}
  - [x] 4.4 Create `app/templates/base.html` with Tailwind CSS CDN and responsive layout structure
  - [x] 4.5 Create `app/templates/storefront.html` with Jinja2 template for rendering storefront pages
  - [x] 4.6 Create `app/static/css/styles.css` with custom CSS overrides and theme variables
  - [x] 4.7 Create `app/static/js/storefront.js` with JavaScript for interactive elements
  - [ ] 4.8 Create `app/ai/__init__.py` (empty file)
  - [ ] 4.9 Create `app/ai/groq_client.py` with Groq API client setup and text generation functions
  - [ ] 4.10 Create `app/ai/page_builder.py` with AI page generation from text input using Kimi k2 model
  - [ ] 4.11 Create `app/ai/migration_wizard.py` with URL scraping for Linktree, Stan.store, Beacons.ai, and goal-based enhancement analysis (revenue, style, traffic optimization) with improvement metrics calculation
  - [ ] 4.12 Create `app/services/unsplash.py` with Unsplash API integration for placeholder images
  - [ ] 4.13 Create `app/routers/ai.py` with endpoints: POST /ai/generate-page, POST /ai/migrate-page, POST /ai/analyze-url
  - [ ] 4.14 Create drag-and-drop page builder frontend components in `app/static/js/page-builder.js` with blocks: header, product, link, contact, scheduler
  - [ ] 4.15 Create theme system in `app/services/theme.py` with Light, Dark, and Creator-brand color picker presets
  - [ ] 4.16 Implement SEO optimization in `app/utils/seo.py` with meta tags, structured data, and sitemap generation

- [ ] 5.0 Product Management and Types Implementation
  - [ ] 5.1 Create `app/schemas/product.py` with ProductCreate, ProductUpdate, ProductResponse, and type-specific schemas
  - [ ] 5.2 Create `app/services/product.py` with CRUD operations for all product types
  - [ ] 5.3 Create `app/routers/product.py` with endpoints: POST /products, GET /products, PUT /products/{id}, DELETE /products/{id}
  - [ ] 5.4 Create `app/services/file_storage.py` with AWS S3 integration using boto3 for digital file uploads
  - [ ] 5.5 Create `app/models/digital_product.py` extending Product for file_url, file_size, download_limit
  - [ ] 5.6 Create `app/models/physical_product.py` extending Product for weight, dimensions, shipping_required
  - [ ] 5.7 Create `app/models/service_product.py` extending Product for duration, calendar_link, booking_url
  - [ ] 5.8 Create `app/models/membership.py` with Membership model for recurring billing (id, product_id, billing_interval, trial_days)
  - [ ] 5.9 Create `app/models/tip_product.py` with TipProduct model for donations and tips (id, product_id, suggested_amounts, allow_custom_amount)
  - [ ] 5.10 Create `