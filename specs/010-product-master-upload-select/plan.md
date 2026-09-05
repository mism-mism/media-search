# Plan: Product master + upload select

1. Domain `Product` + port `ProductRepositoryPort`
2. sqlite `products(product_id PK, name)` + adapter
3. `LibraryService` / API: CRUD products; upload Form `product_id`
4. UI: product list/create; upload `<select>` optional
5. Tests: create, upload binds id, delete blocked when in use
