# Entity-Relationship Diagram

MySQL 8, InnoDB, utf8mb4.

```mermaid
erDiagram
    operator |o--o{ ticket : "assigned to"
    ticket ||--o{ ticket_history : "has events"

    operator {
        INT id PK "AUTO_INCREMENT"
        VARCHAR_100 name "NOT NULL"
        VARCHAR_150 email "NOT NULL, UNIQUE"
        DATETIME created_at "NOT NULL, DEFAULT CURRENT_TIMESTAMP"
    }

    ticket {
        INT id PK "AUTO_INCREMENT, starts at 1001"
        VARCHAR_120 title "NOT NULL"
        VARCHAR_1000 description "NULL"
        VARCHAR_40 asset_code "NOT NULL"
        VARCHAR_10 priority "NOT NULL, DEFAULT MEDIUM, CHECK"
        VARCHAR_20 status "NOT NULL, DEFAULT PENDING, CHECK"
        VARCHAR_1000 diagnosis "NULL"
        INT assigned_operator_id FK "NULL, ON DELETE SET NULL"
        VARCHAR_100 reported_by "NOT NULL"
        DATETIME_3 created_at "NOT NULL, DEFAULT CURRENT_TIMESTAMP_3"
        DATETIME_3 updated_at "NOT NULL, ON UPDATE CURRENT_TIMESTAMP_3"
        INT version "NOT NULL, DEFAULT 1"
    }

    ticket_history {
        BIGINT id PK "AUTO_INCREMENT"
        INT ticket_id FK "NOT NULL, ON DELETE RESTRICT, ON UPDATE CASCADE"
        VARCHAR_20 event_type "NOT NULL, CHECK"
        VARCHAR_20 from_status "NULL"
        VARCHAR_20 to_status "NULL"
        VARCHAR_1000 comment "NULL"
        VARCHAR_100 actor "NOT NULL"
        DATETIME_3 created_at "NOT NULL, DEFAULT CURRENT_TIMESTAMP_3"
    }

    allowed_transition {
        VARCHAR_20 from_status PK "composite PK"
        VARCHAR_20 to_status PK "composite PK"
        TINYINT_1 requires_diagnosis "NOT NULL, DEFAULT 0"
        TINYINT_1 requires_comment "NOT NULL, DEFAULT 0"
    }
```

Type suffixes are lengths (`VARCHAR_100` = `VARCHAR(100)`, `DATETIME_3` = `DATETIME(3)`), because Mermaid attribute types cannot contain parentheses.

## Notes

- `ticket` to `ticket_history` is 1-N and the history is mandatory: `sp_create_ticket` inserts the ticket and its `CREATED` event in one transaction, so every ticket has at least one event.
- `operator` to `ticket` is optional on both sides: a ticket may be unassigned, an operator may have no tickets.
- `allowed_transition` is a lookup table with no FK. `status` is a closed enum enforced by a `CHECK` constraint on `ticket`, so an FK would add no safety. The table only holds the rules (`requires_diagnosis`, `requires_comment`) read by `sp_change_ticket_status`.
- `event_type` values: `CREATED`, `STATUS_CHANGED`, `COMMENT`, `ASSIGNED`.
- Indexes: `ticket(status)`, `ticket(created_at)`, `ticket(assigned_operator_id)`, `ticket_history(ticket_id, created_at)`, `ticket_history(event_type, created_at)`.

## Integrity rules

- `ticket_history.ticket_id` FK is `ON DELETE RESTRICT`: a ticket with history cannot be deleted.
- History is append-only: app code never runs UPDATE or DELETE on `ticket_history`.
- `CHECK` constraints: `ticket.priority` in (LOW, MEDIUM, HIGH, CRITICAL), `ticket.status` in (PENDING, IN_PROGRESS, RESOLVED, CANCELLED), `ticket_history.event_type` in (CREATED, STATUS_CHANGED, COMMENT, ASSIGNED).
- `ticket.assigned_operator_id` is `ON DELETE SET NULL`: removing an operator unassigns their tickets.
- Optimistic concurrency: `ticket.version` starts at 1 and is incremented on every status change or assignment. The caller sends the expected version; a mismatch raises `CONCURRENCY_CONFLICT`.
- Row lock: `sp_change_ticket_status` reads the ticket with `SELECT ... FOR UPDATE` inside the transaction.
