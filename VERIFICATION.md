# Verification report

Verified locally on 14 September 2026 using Python 3.14, Django 6.0.8 and Microsoft Edge through Playwright. The development server was also opened and inspected with agent-browser.

## Results

| Check | Result |
|---|---|
| `python manage.py check` | Passed, no issues |
| Initial migrations | Applied successfully to the demo SQLite database |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `python manage.py test` | 30 tests passed |
| `npm run build:css` | Tailwind CSS compiled successfully |
| `npm run test:browser` | 11 browser workflow groups passed |
| Responsive layouts | No horizontal page overflow at 375px, 768px and 1440px on the inspected routes |
| Images | No broken images on inspected routes; all seeded menu/category images opened successfully in the seed test |
| Browser errors | No JavaScript, console or HTTP 5xx errors during the browser workflow |

## Browser workflows exercised

1. Public routes, image loads and screenshots at mobile, tablet and desktop widths.
2. Menu search, category filter, price filter, sort and pagination using the rendered controls.
3. Guest cart, registration, automatic cart merge, Large / Iced / 50% options, quantity update and removal.
4. Checkout, Pending order, success page, order detail, order history, profile editing and logout.
5. Admin login, responsive Dashboard routes, mobile sidebar and order transitions to Preparing and Ready.
6. Menu creation using all form controls, uploaded image preview, saved image, editing price/stock and verifying the storefront.
7. Delete modal: cancel preserves the item; confirmation deletes it.
8. Category creation, details, editing and deletion.
9. User creation, details, editing with blank password, disabling, enabling and deletion.
10. Customer sees Ready, is denied Dashboard access, and can request a reset link through the console email backend.
11. Browser error collection remains empty.

## Backend invariants tested

- Hashed passwords, weak/invalid/duplicate registration rejection, disabled login and safe login redirects.
- Role protection on every Dashboard resource route and object ownership for carts/orders/profile.
- POST-only mutations and CSRF enforcement.
- Non-negative price/stock; positive quantity; option validation and combined stock limits.
- Atomic stock deduction with rollback if any item cannot be fulfilled.
- Expired checkout token rejection and duplicate checkout idempotency.
- Historical item name and price snapshots; order item retention when a menu is deleted.
- Permitted order transitions and exactly-once restocking on cancellation.
- Image upload decoding plus rejection of fake image files and disallowed extensions.
- User password reset/retention and protection against deleting/disabling/demoting oneself.
- Category deletion protection while it still contains menu items.
- Full password reset token flow and new password verification.
- Idempotent seed: 28 menus / 6 categories / 2 demo accounts, preserving edited prices, stock, category names and passwords.

Browser tests create separate SQLite/media files under `test-results/` and do not change the main demo database. Generated screenshots and `browser-results.json` can be recreated with `npm run test:browser`.

The live demo has no seeded orders, so the first classroom order starts at MC00001. Password-reset emails are intentionally printed to the development terminal. No external email delivery, production deployment, real payment or multi-worker load test was performed.
