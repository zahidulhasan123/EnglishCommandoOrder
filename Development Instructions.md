# Build a Production-Ready Django Book Order Management & Admin System

You are an expert Django architect and senior backend engineer.

I am building a book-selling system where the **customer-facing landing page is already built separately using React**. Your job is to build the **Django backend and a highly customized Django Admin-based management system** for managing books, orders, customers, courier shipments, reports, staff users, and operational workflows.

Do NOT create a separate React/Vue admin dashboard unless absolutely necessary. The primary admin interface should be a **customized Django Admin** with custom templates, buttons, actions, filters, dashboards, reports, and responsive styling.

The system must be designed for production use and should be capable of handling a large number of orders.

---

# 1. First: Analyze the Existing Project

Before writing code:

1. Inspect the entire existing Django project.
2. Identify:

   * Django version
   * Python version
   * Existing apps
   * Existing models
   * Existing settings
   * Database configuration
   * Existing REST API setup
   * Authentication
   * Existing admin customizations
   * Environment variable structure
   * Existing frontend/API integration
3. Do NOT overwrite or unnecessarily restructure existing functionality.
4. Reuse existing architecture where appropriate.
5. Identify conflicts with the requirements below.
6. Create a short implementation plan before making major changes.
7. Then implement the system incrementally.

If important functionality already exists, extend it instead of duplicating it.

---

# 2. Overall Architecture

Use this architecture:

React Landing Pages
|
| REST API
v
Django + Django REST Framework
|
+---- MySQL
|
+---- Django Admin
|
+---- Courier Service
|
+---- Celery + Redis
|
+---- Reporting / Export System

The React frontend should communicate with Django through secure REST APIs.

The React application must NEVER directly communicate with Steadfast or expose courier API credentials.

---

# 3. Core Business Concept

The system sells books using COD-oriented orders.

Customers submit:

* Name
* Phone
* Optional secondary phone
* Address
* Book
* Quantity
* Optional note

The React landing page sends this information to Django.

Django creates an order.

Administrators manage the order through Django Admin.

An administrator can send a confirmed order to Steadfast with one click.

Courier information must be stored against the order.

---

# 4. Applications

Organize the project into logical Django apps if appropriate.

Suggested structure:

apps/
accounts/
books/
orders/
customers/
courier/
reports/
core/

Do not create unnecessary apps if the existing project architecture makes a different structure more appropriate.

---

# 5. Books

Create a robust Book model.

Fields should include approximately:

* title
* slug
* author
* description
* cover_image
* sku
* price
* discount_price
* stock_quantity
* low_stock_threshold
* active
* created_at
* updated_at

Consider:

* indexed slug
* indexed SKU
* database constraints
* sensible decimal handling for money

The system should support multiple books.

Do not hard-code a single book.

---

# 6. Landing Page / Campaign Source

Orders may originate from multiple React landing pages.

The system should be able to identify where an order came from.

Store information such as:

* landing_page
* landing_page_slug
* source
* campaign
* utm_source
* utm_medium
* utm_campaign
* utm_term
* utm_content
* referrer
* user_agent
* IP address where legally/operationally appropriate

Do not unnecessarily store sensitive information.

This will allow reporting such as:

"Which landing page generated the most orders?"

and:

"Which Facebook campaign generated the most revenue?"

---

# 7. Customer Model

Create a reusable Customer model rather than storing all customer information only inside Order.

Fields:

* name
* phone
* secondary_phone
* address
* city/area where appropriate
* created_at
* updated_at

Normalize phone numbers where possible.

Use indexes for phone numbers.

A customer should be identifiable through their phone number.

When a new order comes in:

1. Check whether the customer already exists.
2. Reuse the existing customer where appropriate.
3. Update customer information carefully.
4. Keep historical order information intact.

---

# 8. Customer History

Inside Django Admin, when viewing a customer, show:

* Total orders
* Delivered orders
* Cancelled orders
* Returned orders
* Total purchase value
* Last order date
* Previous orders

For an order, show a customer summary:

Customer:

```
Md. Rahim
```

Phone:

```
017XXXXXXXX
```

Previous Orders:

```
7
```

Delivered:

```
5
```

Cancelled:

```
1
```

Returned:

```
1
```

Total Spent:

```
৳4,500
```

Make previous orders clickable.

---

# 9. Order Model

Create a robust Order model.

Recommended fields:

* order_number
* customer
* book
* quantity
* unit_price
* discount_amount
* delivery_charge
* total_amount
* customer_note
* admin_note
* status
* payment_method
* payment_status
* source
* landing_page
* campaign information
* created_at
* updated_at
* confirmed_at
* cancelled_at
* delivered_at

Use DecimalField for monetary values.

Never use floating point for money.

Order number should be human-friendly, for example:

ORD-20260814-000123

or another scalable format.

Do not use the database primary key directly as the public order number.

---

# 10. Order Status Workflow

Implement clear statuses.

Recommended:

NEW
CONFIRMED
PROCESSING
READY_TO_SHIP
SHIPPED
DELIVERED
CANCELLED
DELIVERY_FAILED
RETURNED

Use a controlled state transition system.

Avoid allowing arbitrary invalid status changes.

For example:

NEW
-> CONFIRMED
-> CANCELLED

CONFIRMED
-> PROCESSING
-> CANCELLED

PROCESSING
-> READY_TO_SHIP

READY_TO_SHIP
-> SHIPPED

SHIPPED
-> DELIVERED
-> DELIVERY_FAILED
-> RETURNED

Allow administrators to make appropriate corrections through a controlled mechanism.

Record every important status change in the activity log.

---

# 11. Order Admin List

Customize Django Admin's Order list extensively.

Columns should include:

* Order number
* Customer
* Phone
* Book
* Quantity
* Total
* Status
* Courier status
* Created date
* Quick action

Provide:

* Search
* Filters
* Date filters
* Status filters
* Book filters
* Courier filters
* Source filters

Search by:

* Order number
* Customer name
* Phone
* Secondary phone
* Tracking code
* Consignment ID
* Address

Use efficient database queries.

Avoid N+1 queries.

Use select_related/prefetch_related where appropriate.

---

# 12. Pagination

The order list must use server-side pagination.

Default:

50 orders per page.

Allow administrators to change page size if appropriate.

Do NOT load thousands of orders into the browser.

The system must remain fast with hundreds of thousands of orders.

---

# 13. One-Click Steadfast Integration

Implement a proper courier service abstraction.

Do not place all Steadfast API code directly inside admin.py.

Create something similar to:

courier/services.py

or:

courier/steadfast.py

Use a service layer.

Example conceptual structure:

OrderAdmin
|
v
CourierService
|
v
SteadfastClient
|
v
Steadfast API

Use environment variables for credentials.

Example:

STEADFAST_API_BASE_URL=
STEADFAST_API_KEY=
STEADFAST_SECRET_KEY=

Never commit credentials.

---

# 14. Send to Steadfast Button

Add a prominent button to the Order Admin detail page:

"Send to Steadfast"

Before sending:

* Validate customer name
* Validate phone
* Validate address
* Validate COD amount
* Validate order status
* Check whether the order was already sent

If already sent, DO NOT create another courier order.

Show:

"Already sent to Steadfast"

with the existing consignment information.

---

# 15. Duplicate Courier Protection

This is critical.

The system must prevent:

Admin clicks Send
Admin clicks Send again
Two courier shipments are created.

Use database-level protection where possible.

Store:

* courier
* consignment_id
* tracking_code
* courier_order_id
* courier_status
* courier_response
* created_at
* updated_at

Use idempotent logic.

If a courier request times out, do not blindly retry in a way that can create duplicate shipments.

Design retry handling carefully.

---

# 16. Courier Shipment Model

Create a separate CourierShipment model.

It should support future couriers.

Do not design the database only around Steadfast.

Example:

CourierShipment

* order
* courier
* external_order_id
* consignment_id
* tracking_code
* delivery_status
* cod_amount
* raw_response
* error_message
* created_at
* updated_at

Initially:

courier = STEADFAST

But design the architecture so future providers such as Pathao, RedX, Paperfly, etc. can be added without rewriting the order system.

---

# 17. Courier Status Synchronization

Design the system to support courier status synchronization.

Eventually a background task should:

1. Find active shipments.
2. Ask courier API for latest status.
3. Update shipment status.
4. Update order status where appropriate.
5. Record the change.

Use Celery for background jobs.

Do not make every admin page request wait for external courier API calls.

---

# 18. Order Admin Actions

Implement useful bulk actions.

Examples:

* Mark as Confirmed
* Mark as Processing
* Mark as Ready to Ship
* Cancel Selected
* Export Selected
* Print Selected Invoices
* Send Selected Orders to Steadfast

Be careful with bulk courier actions.

Validate every order individually.

Do not send cancelled or already-shipped orders.

Show a summary before bulk courier submission.

---

# 19. Order Detail Admin UI

Customize the Order change form so it feels like an operations dashboard rather than a raw Django form.

Organize into sections:

CUSTOMER

* Name
* Phone
* Secondary phone
* Address
* Customer history

ORDER

* Order number
* Book
* Quantity
* Unit price
* Discount
* Delivery charge
* Total

STATUS

* Current status
* Payment status
* Status history

COURIER

* Courier
* Consignment ID
* Tracking ID
* Courier status
* Shipment date

NOTES

* Customer note
* Admin note

ACTIONS

* Send to Steadfast
* Sync Courier Status
* Print Invoice
* Cancel Order

Use clear visual indicators for statuses.

---

# 20. Admin Dashboard

Customize the Django Admin index page.

Create a useful operational dashboard.

Show cards for:

TODAY

* Orders
* Revenue
* Delivered
* Cancelled
* Returned
* Pending

THIS WEEK

* Orders
* Revenue
* Delivered
* Cancellation rate

THIS MONTH

* Orders
* Revenue
* Delivered
* Returned
* Average order value

Also show:

* Orders awaiting confirmation
* Orders ready to ship
* Orders currently in transit
* Delivery failures
* Low stock books

Use database aggregation rather than loading every order into Python.

---

# 21. Daily Report

Create a dedicated reporting section.

Daily report should support selecting a date.

Show:

* Total orders
* New orders
* Confirmed orders
* Shipped orders
* Delivered orders
* Cancelled orders
* Returned orders
* Delivery failed
* Gross sales
* Discounts
* Delivery charges
* Net order value
* Average order value
* Number of books sold
* Orders by book
* Orders by landing page
* Orders by campaign
* Orders by source

Show a summary table.

Example:

Date: 14 August 2026

Orders: 245
Books Sold: 278
Sales: ৳185,500
Delivered: 172
Cancelled: 21
Returned: 8

---

# 22. Weekly Report

Allow:

* Current week
* Previous week
* Custom date range

Show:

* Total orders
* Total sales
* Delivered orders
* Cancelled orders
* Returned orders
* Average daily orders
* Average order value
* Best-selling books
* Best-performing landing pages
* Best-performing campaigns

Show a daily breakdown:

Date | Orders | Books | Sales | Delivered | Cancelled

---

# 23. Monthly Report

Allow selecting:

* Month
* Year

Show:

* Total orders
* Total books sold
* Total revenue
* Delivered revenue
* Cancelled amount
* Returned amount
* Average order value
* Delivery success rate
* Cancellation rate
* Return rate

Show:

Top books.

Top landing pages.

Top campaigns.

Top customer locations if the data exists.

---

# 24. Custom Date Range Reports

Allow admin to select:

From:
[ date ]

To:
[ date ]

Generate report.

This is important for accounting and marketing analysis.

---

# 25. Report Export

Reports must be exportable.

Support:

CSV
Excel/XLSX
PDF where practical

Exports should respect selected filters.

For example:

Date:
1 August → 14 August

Status:
Delivered

Book:
Python Book

Export:

[ Excel ]

The exported file should contain useful columns such as:

* Order number
* Customer
* Phone
* Book
* Quantity
* Amount
* Status
* Courier
* Tracking
* Created date
* Delivered date
* Source
* Campaign

For very large exports, use a background task instead of blocking the web request.

---

# 26. Financial/Sales Reporting

Create a clear distinction between:

* Order value
* Discount
* Delivery charge
* Collected COD amount
* Cancelled value
* Returned value

Do not incorrectly label total order value as profit.

If profit calculation is implemented later, add:

* Cost price
* Courier cost
* Other cost
* Profit

For now, report revenue/order value accurately.

---

# 27. Delivery Analytics

Create metrics:

Delivery success rate:

Delivered / shipped orders

Cancellation rate:

Cancelled / total orders

Return rate:

Returned / shipped orders

Failed delivery rate:

Delivery failed / shipped orders

Show these in reports.

Be explicit about denominators.

Do not create misleading statistics.

---

# 28. Book Analytics

For each book show:

* Orders
* Units sold
* Revenue
* Delivered units
* Cancelled units
* Returned units
* Current stock
* Low-stock warning

Admin should be able to identify best-selling books.

---

# 29. Landing Page Analytics

Track:

* Orders per landing page
* Sales per landing page
* Conversion count if visitor information is available
* Orders by UTM source
* Orders by UTM medium
* Orders by campaign

Example:

Facebook
1,250 orders
৳875,000 sales

Google
420 orders
৳315,000 sales

Direct
180 orders
৳120,000 sales

Do not claim conversion rate unless actual visitor/session data is being tracked.

---

# 30. Customer Analytics

Show:

* New customers
* Returning customers
* Repeat order rate
* Top customers by order count
* Top customers by value
* Customers with many cancellations
* Customers with many returns

Be careful with fraud/risk labeling. Use objective metrics rather than subjective assumptions.

---

# 31. Suspicious Order Warning

Provide operational warnings, not automatic accusations.

Examples:

"Phone number has 8 previous orders and 5 cancellations."

"Customer has 3 failed deliveries."

"Same phone has multiple active orders."

Display:

WARNING

but allow the admin to make the decision.

Do not automatically block customers unless a separate configurable blacklist feature is implemented.

---

# 32. Customer Duplicate Detection

When creating an order:

If the phone number already exists:

show:

Returning customer

Previous orders: 8

Delivered: 6

Cancelled: 1

Returned: 1

If multiple active orders exist for the same phone, show an operational warning.

---

# 33. Phone Number Management

Support:

* Primary phone
* Secondary phone

Admin must be able to edit both.

Normalize Bangladesh phone numbers where appropriate.

Do not destroy the original customer history when phone information changes.

Keep audit logs.

---

# 34. Activity / Audit Log

Create an audit system.

Record:

* Who created the order
* Who edited it
* Who changed status
* Who changed phone number
* Who changed address
* Who sent it to courier
* Who cancelled it
* Who changed courier information

Example:

14:25 — Order created
14:28 — Rahim changed phone
14:30 — Admin confirmed order
14:33 — Sent to Steadfast
14:34 — Consignment created

Store:

* user
* timestamp
* action
* model
* object ID
* old value
* new value

Do not log sensitive credentials.

---

# 35. Invoice

Create a printable invoice.

Include:

* Company name
* Company logo if available
* Order number
* Date
* Customer
* Phone
* Address
* Book
* Quantity
* Price
* Delivery charge
* Discount
* Total
* Payment method
* COD amount

Create a clean print layout.

Also support bulk invoice printing.

---

# 36. Packing Slip

Create a simple packing slip containing:

* Order number
* Customer name
* Phone
* Address
* Book
* Quantity
* Courier
* Consignment ID

Optimize it for printing.

---

# 37. Staff Roles

Use Django permissions/groups.

Suggested roles:

SUPER ADMIN

Everything.

ORDER MANAGER

* View orders
* Edit orders
* Confirm orders
* Cancel orders
* Send courier

COURIER MANAGER

* View shipment information
* Send courier
* Sync courier status

BOOK MANAGER

* Manage books
* Manage inventory

REPORT MANAGER

* View reports
* Export reports

Do not give every staff member unrestricted permissions.

---

# 38. Security

Implement:

* CSRF protection
* Authentication
* Permission checks
* Secure cookies
* Environment variables
* No API secrets in frontend
* Input validation
* Rate limiting for public order APIs if appropriate
* Protection against duplicate order submission
* Database constraints
* Secure production settings

Do not trust any value coming from React.

The backend must validate:

* Book
* Price
* Quantity
* Customer data
* Delivery charge
* Total

IMPORTANT:

Never allow the React client to decide the final price.

React may send the book ID and quantity.

Django must calculate the actual price from the database.

---

# 39. Duplicate Order Protection

Customers may double-click the Order button.

Prevent accidental duplicate orders.

Consider:

* frontend button disabling
* idempotency key
* server-side duplicate detection
* transaction.atomic()

Do not rely only on the frontend.

---

# 40. API Design

Create clean REST API endpoints.

Examples:

POST /api/orders/

GET /api/books/

GET /api/books/{slug}/

GET /api/orders/{order_number}/

If tracking is exposed publicly later:

GET /api/tracking/{order_number}/

Use serializers and validation.

Do not expose unnecessary customer information.

---

# 41. Background Tasks

Use Celery + Redis for:

* Courier status synchronization
* Large report generation
* Large Excel exports
* Bulk courier submission
* Notifications
* Scheduled daily reports
* Other long-running jobs

Do not make a normal admin request wait for a slow external API if it can be safely handled asynchronously.

---

# 42. Database Performance

Design for large datasets.

Add indexes to frequently searched/filtered fields:

* order_number
* customer phone
* status
* created_at
* book
* courier status
* consignment ID
* tracking code
* landing page
* campaign

Use:

select_related()

prefetch_related()

database aggregation:

Count
Sum
Avg

Do not retrieve all orders and calculate reports in Python.

Reports must use efficient database queries.

---

# 43. Soft Delete / Data Retention

Do not casually delete orders.

Orders are business records.

Prefer:

* active/inactive where appropriate
* cancellation
* archival if necessary

Only super-admin should have destructive deletion capabilities.

Consider protecting historical order records from accidental deletion.

---

# 44. Error Handling

Courier failures must be handled gracefully.

If Steadfast API fails:

Show:

Courier submission failed.

Reason:

[API error]

Allow retry.

Do not change order status to SHIPPED if the courier order was not successfully created.

Store an appropriate error message for debugging.

Never expose internal API secrets or sensitive responses to ordinary staff.

---

# 45. Notifications / User Feedback

Admin actions should provide clear Django Admin messages.

Examples:

SUCCESS:

"Order ORD-10251 successfully sent to Steadfast."

ERROR:

"Could not send order to Steadfast. Please try again."

WARNING:

"This order already has a courier shipment."

---

# 46. Admin UI/UX

Make the Django Admin feel professional.

Use:

* Clear section headings
* Status badges
* Action buttons
* Consistent spacing
* Responsive layout
* Useful dashboard cards
* Good empty states
* Confirmation dialogs
* Error messages
* Success messages

Do not sacrifice Django Admin's maintainability just to make it visually flashy.

Prioritize speed and usability.

---

# 47. Dashboard Quick Actions

Add shortcuts:

* New Order

* New Book

View New Orders

View Orders Ready to Ship

View Today's Orders

Today's Report

This Week's Report

This Month's Report

Export Orders

---

# 48. Date & Time

Use timezone-aware Django settings.

The business timezone should be configurable and should support Bangladesh time:

Asia/Dhaka

Do not use naive datetime handling.

Reports must use the correct local business date.

---

# 49. Testing

Create proper automated tests.

Test:

* Order creation
* Price calculation
* Quantity
* Duplicate submission
* Customer matching
* Status transitions
* Courier submission
* Duplicate courier prevention
* Failed courier submission
* Report calculations
* Date boundaries
* Export functionality
* Permissions
* Authentication
* API validation

Mock the Steadfast API in tests.

Never make real courier API calls during automated tests.

---

# 50. Important Edge Cases

Handle:

* Duplicate order submission
* Same phone with multiple orders
* Missing secondary phone
* Invalid phone
* Invalid quantity
* Book becoming inactive
* Book price changing after order
* Courier API timeout
* Courier API returning an error
* Admin clicking courier button twice
* Cancelled order attempting courier submission
* Already shipped order attempting another shipment
* Large report export
* Large order list
* Deleted/inactive books associated with historical orders

Historical orders should retain their original unit price.

If a book price changes from ৳500 to ৳600, old orders must remain ৳500.

---

# 51. Production Quality

Follow:

* PEP 8
* Django best practices
* Type hints where useful
* Service layer for business logic
* Reusable utilities
* Clear model methods
* Database constraints
* Transactions
* Proper logging
* Environment variables
* Documentation

Avoid:

* giant admin.py files
* business logic scattered throughout views
* hard-coded credentials
* hard-coded prices
* hard-coded courier logic
* N+1 queries
* unnecessary API calls
* duplicated code

---

# 52. Suggested Service Structure

Where appropriate:

services/
order_service.py
customer_service.py
courier_service.py
report_service.py

courier/
base.py
steadfast.py

This should make it easy to add another courier later.

Example conceptual interface:

CourierService.create_shipment(order)

CourierService.get_status(shipment)

CourierService.cancel_shipment(shipment)

Steadfast implements this interface initially.

---

# 53. Reporting Architecture

Reports should not be hard-coded into individual admin methods.

Create reusable report services.

Example:

DailySalesReport
WeeklySalesReport
MonthlySalesReport
CustomRangeSalesReport

Each report should provide structured data.

Then the same report data can be used by:

* Django Admin
* CSV export
* Excel export
* PDF export
* Future API
* Future analytics dashboard

This avoids duplicated business logic.

---

# 54. Export Architecture

Implement export services rather than writing export logic separately for every button.

For example:

ExportService.export_orders(...)
ExportService.export_daily_report(...)
ExportService.export_monthly_report(...)

For small exports:

Generate immediately.

For large exports:

Queue a Celery task and notify the admin when complete.

---

# 55. Report Dashboard UI

Create an admin reports section such as:

Reports

```
Daily Report
Weekly Report
Monthly Report
Custom Report
Book Performance
Landing Page Performance
Courier Performance
Customer Report
```

Each report should have:

Filters
Summary cards
Tables
Export buttons

---

# 56. Courier Performance Report

Show:

* Total shipments
* Delivered
* In transit
* Failed
* Returned
* Delivery success rate
* Return rate

Eventually support multiple courier providers.

---

# 57. Inventory Alerts

On the dashboard show:

LOW STOCK

Python Book
Remaining: 8

IELTS Book
Remaining: 12

CRITICAL STOCK

Grammar Book
Remaining: 2

Do not allow negative stock unless explicitly configured.

---

# 58. Future Extensibility

The architecture should make it easy to add:

* Payment gateways
* More couriers
* SMS
* WhatsApp notifications
* Email
* Inventory management
* Multiple warehouses
* Multiple currencies
* Coupons
* Promotions
* Full ecommerce/cart functionality
* Public order tracking
* Mobile application

Do not implement all of these now.

Build the foundation so they can be added later.

---

# 59. Documentation

Create/update:

README.md

Include:

* Project architecture
* Setup instructions
* Environment variables
* Database setup
* Redis setup
* Celery setup
* Steadfast configuration
* Running tests
* Running development server
* Production deployment
* Admin usage
* Report generation
* API endpoints

Also document how to configure the React frontend to communicate with Django.

---

# 60. Environment Variables

Use environment variables for:

DATABASE_URL

SECRET_KEY

DEBUG

ALLOWED_HOSTS

CORS_ALLOWED_ORIGINS

REDIS_URL

CELERY_BROKER_URL

CELERY_RESULT_BACKEND

STEADFAST_API_BASE_URL

STEADFAST_API_KEY

STEADFAST_SECRET_KEY

Do not commit real secrets.

Update .env.example with placeholder values.

---

# 61. Deployment Compatibility

The application should be suitable for deployment using Docker/Coolify.

Make sure:

* Static files work correctly
* Media files are properly configured
* PostgreSQL works
* Redis works
* Celery worker works
* Celery beat works if scheduled tasks are implemented
* Environment variables are used
* Production settings are separated appropriately

Do not store uploaded book images in the container filesystem if the project is configured for object storage.

---

# 62. Final Implementation Workflow

Do NOT attempt to generate the entire system blindly in one step.

Work in phases.

PHASE 1

Analyze existing project.

PHASE 2

Implement models and migrations.

PHASE 3

Implement customer/order REST APIs.

PHASE 4

Implement Django Admin order management.

PHASE 5

Implement customized admin dashboard.

PHASE 6

Implement Steadfast integration.

PHASE 7

Implement audit logs.

PHASE 8

Implement reports.

PHASE 9

Implement exports.

PHASE 10

Implement Celery/background processing.

PHASE 11

Implement tests.

PHASE 12

Review security/performance.

PHASE 13

Update documentation.

After each phase:

1. Run tests.
2. Check migrations.
3. Check for errors.
4. Review existing functionality for regressions.
5. Continue only after the previous phase is stable.

---

# 63. Important Development Rule

Before implementing anything, inspect the existing repository.

Do not assume:

* app names
* model names
* database structure
* Django version
* authentication system
* API structure
* deployment setup

Adapt the implementation to the existing project.

Do not replace working code unnecessarily.

---

# 64. Definition of Done

The system is considered complete when:

* React can successfully create orders through Django API.
* Orders appear in Django Admin.
* Orders can be searched and filtered.
* Orders are paginated efficiently.
* Admin can edit customer information.
* Admin can add/edit secondary phone.
* Admin can change order status.
* Admin can view customer history.
* Admin can send eligible orders to Steadfast with one click.
* Duplicate courier submissions are prevented.
* Courier information is stored.
* Courier errors are handled safely.
* Admin can print invoices.
* Admin can perform bulk actions.
* Admin can view daily reports.
* Admin can view weekly reports.
* Admin can view monthly reports.
* Admin can generate custom date-range reports.
* Reports can be exported.
* Book performance can be analyzed.
* Landing-page/campaign performance can be analyzed.
* Activity logs record important changes.
* Staff permissions work correctly.
* Celery handles long-running/background tasks.
* Database queries are optimized.
* Automated tests cover critical workflows.
* Production configuration is documented.
* No secrets are committed.
* The application is suitable for deployment through Docker/Coolify.

---

# 65. Start Now

Start by inspecting the existing repository.

Do not immediately generate code.

First provide:

1. Current project architecture
2. Existing Django apps
3. Existing models relevant to orders/books/users
4. Existing API structure
5. Existing admin structure
6. Recommended implementation plan
7. Potential conflicts or missing dependencies
8. Files you intend to create/change

Then begin implementation phase by phase.

Keep the implementation production-quality, maintainable, secure, scalable, and easy for another Django developer to understand.
