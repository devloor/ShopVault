# Amazon-style Django E-commerce Project

This project is a Django-based e-commerce web application inspired by Amazon. It includes product browsing, search, user accounts, cart and checkout flows, reviews, wishlist features, and order history.

## Project Structure

- `apps.accounts` - user authentication, registration, profile, address management, order history
- `apps.core` - home page, product pages, search, categories, wishlist, review and Q&A pages, static marketing pages
- `apps.products` - product and category models, reviews, wishlist, product images, questions and answers
- `apps.cart` - shopping cart management for anonymous/session users and logged-in users
- `apps.orders` - checkout flow, order creation, order confirmation and order status tracking
- `config` - Django project settings, URLs, and WSGI/ASGI configuration

## Virtual Environment

- The Python virtual environment is located in `.venv`
- Activate it on Windows PowerShell:

```powershell
& ".\.venv\Scripts\Activate.ps1"
```

- The `.env` file is used to store sensitive configuration such as `DJANGO_SECRET_KEY`, social auth credentials, and other environment variables.

## Static Assets & Favicon

- Static files are served from the `static/` directory and collected to `staticfiles/` for deployment.
- `static/css/app.css` now contains the main site styling previously embedded inside `templates/base.html`.
- `static/favicon.svg` is configured in `templates/base.html` and now loads as the site favicon.
- A PWA manifest is available at `static/site.webmanifest` for improved mobile support.
 - `static/favicon.png` is available as a PNG fallback favicon.
 - `static/apple-touch-icon.png` is available for Apple touch homescreen icon support.

## Deployment note

For production, run:

```powershell
& ".\.venv\Scripts\Activate.ps1"
python manage.py collectstatic --noinput
```

Then serve the collected files from the `staticfiles/` directory via your web server.

## Key Features

- Product listing and category browsing
- Search with filters and sort options
- Product detail pages with reviews, gallery images, wishlist, and Q&A
- Cart add/update/remove
- Checkout with stock validation and atomic order processing
- User registration, login, profile editing, address book, order history
- Admin-friendly static pages and staff dashboard hooks

## Suggested Improvements

### Improve the front-end experience
- Add Ajax-based add-to-cart functionality
- Add Ajax-based wishlist toggling
- Add product review sorting/filtering on product pages
- Add search autocomplete or suggestions

### Consider stronger Amazon-style data
- Add more product metadata (brand, features, specs, ratings breakdown)
- Support multiple image thumbnails / gallery view for each product
- Enhance category faceting for richer filter navigation

## Next Steps

If you want, I can also help with:
- a security review
- implementing the Ajax-based cart and wishlist interactions
- adding product review sorting/filtering
- building search autocomplete or suggestions
- improving product metadata and category faceting

## Run the Project

```powershell
& ".\ .venv\Scripts\Activate.ps1"
python manage.py migrate
python manage.py runserver
```

> Note: Ensure `.env` contains the required variables before running the project.
