# Endpoints Integration Guide

Base URL prefix: `/api/v1`

All request/response JSON keys are in **camelCase**.

## Content Type

- Request: `application/json`
- Response: `application/json`
- Error response: `application/problem+json` (RFC7807)

## 1) Process Expense From Chat

- **Method:** `POST`
- **Path:** `/api/v1/chat/process_expense`

### Request body

```json
{
  "text": "Lunch 12.50 at Cafe Central today",
  "provider": "openai",
  "apiKey": "sk-user-key-optional"
}
```

### Request fields

- `text` (string, required)
- `provider` (string, required) — current supported value: `openai`
- `apiKey` (string, optional) — per-request key from mobile app; if absent, backend tries `OPENAI_API_KEY` from environment

### Success response

```json
{
  "saved": true,
  "duplicate": false,
  "expenseId": "b8df1f49-4f81-4bde-a963-c1e7ab2ccdc4",
  "expense": {
    "id": "b8df1f49-4f81-4bde-a963-c1e7ab2ccdc4",
    "amount": 12.5,
    "category": "food",
    "description": "Lunch",
    "providerName": "Cafe Central",
    "expenseDate": "2026-03-31",
    "rawText": "Lunch 12.50 at Cafe Central today",
    "linkedInvoiceId": null,
    "createdAt": "2026-03-31T20:15:41.325000Z"
  }
}
```

### Duplicate response

```json
{
  "saved": false,
  "duplicate": true,
  "expenseId": null,
  "expense": null
}
```

---

## 2) Import Expenses Batch

- **Method:** `POST`
- **Path:** `/api/v1/expenses/import`

### Request body

```json
{
  "invoices": [
    {
      "accessKey": "ABC-123",
      "externalId": "ext-1",
      "invoiceNumber": "INV-001",
      "supplierName": "Tech Store",
      "supplierRuc": "1234567890",
      "issueDate": "2026-03-20",
      "subtotal": 100.0,
      "tax": 12.0,
      "total": 112.0,
      "details": [
        {
          "itemName": "Keyboard",
          "quantity": 1,
          "unitPrice": 100.0,
          "discount": 0,
          "lineSubtotal": 100.0,
          "tax": 12.0,
          "totalLine": 112.0
        }
      ],
      "expenses": [
        {
          "amount": 112.0,
          "category": "equipment",
          "description": "Mechanical keyboard",
          "providerName": "Tech Store",
          "expenseDate": "2026-03-20",
          "rawText": "Keyboard purchase"
        }
      ]
    }
  ]
}
```

### Success response

```json
{
  "invoicesSaved": 1,
  "invoicesSkippedDuplicate": 0,
  "expensesSaved": 1,
  "expensesSkippedDuplicate": 0
}
```

---

## 3) List Expenses

- **Method:** `GET`
- **Path:** `/api/v1/expenses`

### Query params (optional)

- `startDate` (YYYY-MM-DD)
- `endDate` (YYYY-MM-DD)
- `category` (string)
- `providerName` (string)
- `minAmount` (number)
- `maxAmount` (number)
- `search` (string)

### Example

`GET /api/v1/expenses?startDate=2026-03-01&endDate=2026-03-31&providerName=cafe`

### Success response

```json
{
  "items": [
    {
      "id": "b8df1f49-4f81-4bde-a963-c1e7ab2ccdc4",
      "amount": 12.5,
      "category": "food",
      "description": "Lunch",
      "providerName": "Cafe Central",
      "expenseDate": "2026-03-31",
      "rawText": "Lunch 12.50 at Cafe Central today",
      "linkedInvoiceId": null,
      "createdAt": "2026-03-31T20:15:41.325000Z"
    }
  ],
  "total": 1
}
```

---

## 4) Health Check

- **Method:** `GET`
- **Path:** `/health`

### Response

```json
{
  "status": "ok"
}
```

---

## Error Format (RFC7807)

Example:

```json
{
  "type": "urn:expenses:problem:validation",
  "title": "Validation failed",
  "status": 422,
  "instance": "/api/v1/chat/process_expense",
  "detail": "OpenAI API key is required"
}
```

For request validation errors, `errors` array may be present.
