# Sequence Diagrams

## Create ticket

```mermaid
sequenceDiagram
    actor Reporter
    participant FE as Frontend (React)
    participant API as API (FastAPI route)
    participant SVC as TicketService
    participant REPO as TicketRepository
    participant DB as MySQL (SP)

    Reporter->>FE: Fill form and submit
    FE->>API: POST /api/tickets
    API->>API: Validate body (Pydantic)
    alt Validation error
        API-->>FE: 400 ProblemDetails (VALIDATION_ERROR, errors[])
        FE-->>Reporter: Show field errors
    else Valid
        API->>SVC: create_ticket(data)
        SVC->>REPO: create(data)
        REPO->>DB: CALL sp_create_ticket(...)
        Note over DB: START TRANSACTION<br/>INSERT ticket<br/>INSERT ticket_history (CREATED)<br/>COMMIT
        DB-->>REPO: ticket row
        REPO-->>SVC: ticket
        SVC-->>API: Ticket (with allowedTransitions)
        API-->>FE: 201 Ticket
        FE-->>Reporter: Show new ticket code
    end
```

## Change status

```mermaid
sequenceDiagram
    actor Operator
    participant FE as Frontend (React)
    participant API as API (FastAPI route)
    participant SVC as TicketService
    participant REPO as TicketRepository
    participant DB as MySQL (SP)

    Operator->>FE: Pick an allowed transition
    FE->>API: POST /api/tickets/{id}/transitions
    API->>SVC: change_status(id, toStatus, diagnosis, comment, actor, version)
    SVC->>REPO: get(id)
    REPO-->>SVC: ticket
    SVC->>SVC: state_machine.validate(from, to, diagnosis, comment)
    alt Invalid transition or missing diagnosis/comment
        SVC-->>API: DomainError
        API-->>FE: 422 ProblemDetails
        FE-->>Operator: Show error
    else Valid
        SVC->>REPO: change_status(...)
        REPO->>DB: CALL sp_change_ticket_status(...)
        Note over DB: START TRANSACTION<br/>SELECT ... FOR UPDATE<br/>check version<br/>check allowed_transition<br/>UPDATE ticket<br/>INSERT ticket_history (STATUS_CHANGED)<br/>COMMIT
        alt SIGNAL (business error)
            DB-->>REPO: error 1644 (code in MESSAGE_TEXT), ROLLBACK
            REPO-->>SVC: DomainError
            SVC-->>API: DomainError
            API-->>FE: 404 / 409 / 422 ProblemDetails
            FE-->>Operator: Show error
        else OK
            DB-->>REPO: updated ticket row
            REPO-->>SVC: ticket
            SVC-->>API: Ticket
            API-->>FE: 200 Ticket
            FE->>API: GET /api/tickets/{id}/history
            API-->>FE: HistoryEvent[]
            FE-->>Operator: Refresh history and show toast
        end
    end
```
