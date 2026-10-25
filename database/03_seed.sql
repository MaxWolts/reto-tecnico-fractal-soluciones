-- =============================================================================
-- 03_seed.sql
-- Demo data: 3 operators and 5 tickets with coherent history.
-- Target: MySQL 8.0. Run after 01_schema.sql and 02_stored_procedures.sql.
--
-- Rows are inserted directly, not through the stored procedures, because the
-- demo needs deterministic ticket ids (#1028, #1031, #1039, #1042, #1045) and
-- back-dated timestamps. The SPs always use AUTO_INCREMENT and NOW(3).
--
-- Every history walks only rows of allowed_transition, the final ticket status
-- equals the last STATUS_CHANGED to_status, and
-- version = 1 + status changes + assignments.
--
-- Idempotent: it clears demo tables first, so re-running gives the same data.
-- DEV RESET: deletes all operators, tickets and history.
-- (The append-only history rule applies to app code, not to this dev script.)
-- =============================================================================

SET NAMES utf8mb4;

DELETE FROM ticket_history;
DELETE FROM ticket;
DELETE FROM operator;
ALTER TABLE ticket_history AUTO_INCREMENT = 1;
ALTER TABLE operator AUTO_INCREMENT = 1;

-- -----------------------------------------------------------------------------
-- Operators
-- -----------------------------------------------------------------------------
INSERT INTO operator (id, name, email) VALUES
    (1, 'Carlos Quispe Mamani',  'carlos.quispe@example.com'),
    (2, 'Rosa Huaman Torres',    'rosa.huaman@example.com'),
    (3, 'Luis Fernandez Chavez', 'luis.fernandez@example.com');

-- -----------------------------------------------------------------------------
-- Tickets (explicit ids; timestamps relative to NOW(3))
-- updated_at = time of the last status change or assignment.
-- -----------------------------------------------------------------------------
INSERT INTO ticket
    (id, title, description, asset_code, priority, status, diagnosis,
     assigned_operator_id, reported_by, created_at, updated_at, version)
VALUES
    -- RESOLVED after one return to PENDING. 4 status changes + 1 assignment.
    (1028, 'Air conditioning failure',
     'Air conditioning in the main office stopped cooling. Room temperature above 28 C.',
     'SEDE-LIM', 'MEDIUM', 'RESOLVED',
     'Compressor capacitor failed. Replaced capacitor and recharged refrigerant gas.',
     3, 'Maria Salazar',
     NOW(3) - INTERVAL 144 HOUR, NOW(3) - INTERVAL 98 HOUR, 6),

    -- RESOLVED. 2 status changes + 1 assignment.
    (1031, 'Card reader replacement',
     'ATM card reader rejects most cards. Customers report read errors.',
     'ATM-0210', 'MEDIUM', 'RESOLVED',
     'Card reader head worn out. Replaced card reader module and ran test transactions.',
     2, 'Jorge Rojas',
     NOW(3) - INTERVAL 120 HOUR, NOW(3) - INTERVAL 116 HOUR, 4),

    -- IN_PROGRESS, assigned. 1 status change + 1 assignment.
    (1039, 'UPS alarm',
     'UPS in the server room shows a battery alarm and beeps every minute.',
     'SEDE-ARE', 'HIGH', 'IN_PROGRESS', NULL,
     1, 'Ana Torres',
     NOW(3) - INTERVAL 72 HOUR, NOW(3) - INTERVAL 70 HOUR, 3),

    -- PENDING, new.
    (1042, 'ATM out of service',
     'ATM screen is black and it does not dispense cash.',
     'ATM-0451', 'HIGH', 'PENDING', NULL,
     NULL, 'Jorge Rojas',
     NOW(3) - INTERVAL 20 HOUR, NOW(3) - INTERVAL 20 HOUR, 1),

    -- PENDING, new.
    (1045, 'Pipe leak on 2nd floor',
     'Water leak from a ceiling pipe near the 2nd floor restrooms.',
     'SEDE-LIM', 'MEDIUM', 'PENDING', NULL,
     NULL, 'Maria Salazar',
     NOW(3) - INTERVAL 4 HOUR, NOW(3) - INTERVAL 4 HOUR, 1);

-- New tickets created by the app start after the demo range.
ALTER TABLE ticket AUTO_INCREMENT = 1100;

-- -----------------------------------------------------------------------------
-- History (oldest first per ticket)
-- -----------------------------------------------------------------------------
INSERT INTO ticket_history
    (ticket_id, event_type, from_status, to_status, comment, actor, created_at)
VALUES
    -- #1028: PENDING -> IN_PROGRESS -> PENDING -> IN_PROGRESS -> RESOLVED
    (1028, 'CREATED',        NULL,          'PENDING',     NULL,
     'Maria Salazar',         NOW(3) - INTERVAL 144 HOUR),
    (1028, 'ASSIGNED',       NULL,          NULL,          'Assigned to Luis Fernandez Chavez',
     'Luis Fernandez Chavez', NOW(3) - INTERVAL 143 HOUR),
    (1028, 'STATUS_CHANGED', 'PENDING',     'IN_PROGRESS', NULL,
     'Luis Fernandez Chavez', NOW(3) - INTERVAL 142 HOUR),
    (1028, 'STATUS_CHANGED', 'IN_PROGRESS', 'PENDING',     'Waiting for compressor capacitor spare part.',
     'Luis Fernandez Chavez', NOW(3) - INTERVAL 130 HOUR),
    (1028, 'STATUS_CHANGED', 'PENDING',     'IN_PROGRESS', NULL,
     'Luis Fernandez Chavez', NOW(3) - INTERVAL 100 HOUR),
    (1028, 'STATUS_CHANGED', 'IN_PROGRESS', 'RESOLVED',
     'Diagnosis: Compressor capacitor failed. Replaced capacitor and recharged refrigerant gas.',
     'Luis Fernandez Chavez', NOW(3) - INTERVAL 98 HOUR),

    -- #1031: PENDING -> IN_PROGRESS -> RESOLVED
    (1031, 'CREATED',        NULL,          'PENDING',     NULL,
     'Jorge Rojas',           NOW(3) - INTERVAL 120 HOUR),
    (1031, 'ASSIGNED',       NULL,          NULL,          'Assigned to Rosa Huaman Torres',
     'Rosa Huaman Torres',    NOW(3) - INTERVAL 119 HOUR),
    (1031, 'STATUS_CHANGED', 'PENDING',     'IN_PROGRESS', NULL,
     'Rosa Huaman Torres',    NOW(3) - INTERVAL 118 HOUR),
    (1031, 'STATUS_CHANGED', 'IN_PROGRESS', 'RESOLVED',
     'Diagnosis: Card reader head worn out. Replaced card reader module and ran test transactions.',
     'Rosa Huaman Torres',    NOW(3) - INTERVAL 116 HOUR),

    -- #1039: PENDING -> IN_PROGRESS, plus a comment
    (1039, 'CREATED',        NULL,          'PENDING',     NULL,
     'Ana Torres',            NOW(3) - INTERVAL 72 HOUR),
    (1039, 'ASSIGNED',       NULL,          NULL,          'Assigned to Carlos Quispe Mamani',
     'Carlos Quispe Mamani',  NOW(3) - INTERVAL 71 HOUR),
    (1039, 'STATUS_CHANGED', 'PENDING',     'IN_PROGRESS', NULL,
     'Carlos Quispe Mamani',  NOW(3) - INTERVAL 70 HOUR),
    (1039, 'COMMENT',        NULL,          NULL,          'Battery bank is at end of life. Replacement batteries ordered from supplier.',
     'Carlos Quispe Mamani',  NOW(3) - INTERVAL 50 HOUR),

    -- #1042: created only
    (1042, 'CREATED',        NULL,          'PENDING',     NULL,
     'Jorge Rojas',           NOW(3) - INTERVAL 20 HOUR),

    -- #1045: created only
    (1045, 'CREATED',        NULL,          'PENDING',     NULL,
     'Maria Salazar',         NOW(3) - INTERVAL 4 HOUR);
