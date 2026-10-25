-- =============================================================================
-- 01_schema.sql
-- Maintenance ticket system: tables, constraints, indexes and reference data.
-- Target: MySQL 8.0, InnoDB, utf8mb4.
--
-- Run order:
--   01_schema.sql             (this file)
--   02_stored_procedures.sql  (business logic: sp_create_ticket, ...)
--   03_seed.sql               (demo operators and tickets)
--
-- Idempotent: safe to run many times. It drops and recreates every table.
-- =============================================================================

SET NAMES utf8mb4;

-- -----------------------------------------------------------------------------
-- DEV RESET: DROPS ALL DATA.
-- Tables are dropped in FK-safe order (children first) so a re-run always
-- starts from an empty database. Never run this file against production data.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS ticket_history;
DROP TABLE IF EXISTS ticket;
DROP TABLE IF EXISTS allowed_transition;
DROP TABLE IF EXISTS operator;

-- -----------------------------------------------------------------------------
-- operator: maintenance staff that tickets can be assigned to.
-- Note: MySQL always names a primary key PRIMARY; the pk_ name documents intent.
-- -----------------------------------------------------------------------------
CREATE TABLE operator (
    id          INT          NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_operator PRIMARY KEY (id),
    CONSTRAINT uq_operator_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- ticket: one maintenance request. Code shown in UI is "#" + id.
-- version supports optimistic concurrency (incremented on status change and
-- on assignment).
-- -----------------------------------------------------------------------------
CREATE TABLE ticket (
    id                    INT           NOT NULL AUTO_INCREMENT,
    title                 VARCHAR(120)  NOT NULL,
    description           VARCHAR(1000) NULL,
    asset_code            VARCHAR(40)   NOT NULL,
    priority              VARCHAR(10)   NOT NULL DEFAULT 'MEDIUM',
    status                VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    diagnosis             VARCHAR(1000) NULL,
    assigned_operator_id  INT           NULL,
    reported_by           VARCHAR(100)  NOT NULL,
    created_at            DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at            DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                        ON UPDATE CURRENT_TIMESTAMP(3),
    version               INT           NOT NULL DEFAULT 1,
    CONSTRAINT pk_ticket PRIMARY KEY (id),
    CONSTRAINT fk_ticket_assigned_operator
        FOREIGN KEY (assigned_operator_id) REFERENCES operator (id)
        ON DELETE SET NULL,
    CONSTRAINT chk_ticket_priority
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT chk_ticket_status
        CHECK (status IN ('PENDING', 'IN_PROGRESS', 'RESOLVED', 'CANCELLED')),
    INDEX ix_ticket_status (status),
    INDEX ix_ticket_created_at (created_at),
    INDEX ix_ticket_assigned_operator_id (assigned_operator_id)
) ENGINE=InnoDB AUTO_INCREMENT=1001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- ticket_history: append-only event log per ticket.
-- App code never runs UPDATE or DELETE on this table.
-- -----------------------------------------------------------------------------
CREATE TABLE ticket_history (
    id           BIGINT        NOT NULL AUTO_INCREMENT,
    ticket_id    INT           NOT NULL,
    event_type   VARCHAR(20)   NOT NULL,
    from_status  VARCHAR(20)   NULL,
    to_status    VARCHAR(20)   NULL,
    comment      VARCHAR(1000) NULL,
    actor        VARCHAR(100)  NOT NULL,
    created_at   DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_ticket_history PRIMARY KEY (id),
    CONSTRAINT fk_ticket_history_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_ticket_history_event_type
        CHECK (event_type IN ('CREATED', 'STATUS_CHANGED', 'COMMENT', 'ASSIGNED')),
    INDEX ix_ticket_history_ticket_created (ticket_id, created_at),
    INDEX ix_ticket_history_event_created (event_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- allowed_transition: state machine rules read by sp_change_ticket_status.
-- Lookup table, no FK (status is a closed enum checked on ticket).
-- -----------------------------------------------------------------------------
CREATE TABLE allowed_transition (
    from_status         VARCHAR(20) NOT NULL,
    to_status           VARCHAR(20) NOT NULL,
    requires_diagnosis  TINYINT(1)  NOT NULL DEFAULT 0,
    requires_comment    TINYINT(1)  NOT NULL DEFAULT 0,
    CONSTRAINT pk_allowed_transition PRIMARY KEY (from_status, to_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Reference data (not demo seed): the only valid status transitions.
-- RESOLVED and CANCELLED are final, so they have no outgoing rows.
-- -----------------------------------------------------------------------------
INSERT INTO allowed_transition (from_status, to_status, requires_diagnosis, requires_comment) VALUES
    ('PENDING',     'IN_PROGRESS', 0, 0),
    ('PENDING',     'CANCELLED',   0, 1),
    ('IN_PROGRESS', 'RESOLVED',    1, 0),
    ('IN_PROGRESS', 'PENDING',     0, 1),
    ('IN_PROGRESS', 'CANCELLED',   0, 1);
