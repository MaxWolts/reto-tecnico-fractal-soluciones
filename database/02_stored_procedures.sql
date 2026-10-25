-- =============================================================================
-- 02_stored_procedures.sql
-- Business logic for the maintenance ticket system.
-- Target: MySQL 8.0. Run after 01_schema.sql.
--
-- Every procedure runs in one transaction. Any error rolls back and is
-- re-raised to the caller. Business errors use:
--   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '<CODE>'   (MySQL errno 1644)
--
-- Procedures that return a ticket select the ticket read model columns:
--   t.id, t.title, t.description, t.asset_code, t.priority, t.status,
--   t.diagnosis, t.assigned_operator_id, o.name AS assigned_operator_name,
--   t.reported_by, t.created_at, t.updated_at, t.version
-- The result is selected after COMMIT, so it shows committed data.
--
-- Blank text input (NULL, '' or only spaces) is normalized to NULL with
-- NULLIF(TRIM(x), '').
--
-- Idempotent: safe to run many times (DROP PROCEDURE IF EXISTS first).
-- =============================================================================

SET NAMES utf8mb4;

-- -----------------------------------------------------------------------------
-- sp_create_ticket
-- Creates a PENDING ticket and its CREATED history event.
-- priority defaults to MEDIUM when blank.
-- Errors: no business codes. Constraint errors (NOT NULL 1048, CHECK 3819,
-- data too long 1406) are re-raised as is.
-- Result: the new ticket (read model).
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_create_ticket;

DELIMITER $$

CREATE PROCEDURE sp_create_ticket(
    IN p_title        VARCHAR(120),
    IN p_description  VARCHAR(1000),
    IN p_asset_code   VARCHAR(40),
    IN p_priority     VARCHAR(10),
    IN p_reported_by  VARCHAR(100)
)
BEGIN
    DECLARE v_ticket_id   INT DEFAULT NULL;
    DECLARE v_reported_by VARCHAR(100) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_reported_by = NULLIF(TRIM(p_reported_by), '');

    START TRANSACTION;

    INSERT INTO ticket (title, description, asset_code, priority, status, reported_by)
    VALUES (
        NULLIF(TRIM(p_title), ''),
        NULLIF(TRIM(p_description), ''),
        NULLIF(TRIM(p_asset_code), ''),
        COALESCE(NULLIF(TRIM(p_priority), ''), 'MEDIUM'),
        'PENDING',
        v_reported_by
    );

    SET v_ticket_id = LAST_INSERT_ID();

    INSERT INTO ticket_history (ticket_id, event_type, from_status, to_status, comment, actor)
    VALUES (v_ticket_id, 'CREATED', NULL, 'PENDING', NULL, v_reported_by);

    COMMIT;

    SELECT t.id, t.title, t.description, t.asset_code, t.priority, t.status,
           t.diagnosis, t.assigned_operator_id, o.name AS assigned_operator_name,
           t.reported_by, t.created_at, t.updated_at, t.version
      FROM ticket t
      LEFT JOIN operator o ON o.id = t.assigned_operator_id
     WHERE t.id = v_ticket_id;
END$$

DELIMITER ;

-- -----------------------------------------------------------------------------
-- sp_change_ticket_status
-- Moves a ticket to another status, following the rules in allowed_transition.
-- Locks the ticket row (FOR UPDATE) so concurrent changes are serialized.
-- A given diagnosis is stored on the ticket (blank keeps the current one).
-- History comment = the comment, or "Diagnosis: <text>" when only a
-- diagnosis is given.
-- Errors (checked in this order):
--   TICKET_NOT_FOUND      no ticket with p_ticket_id
--   CONCURRENCY_CONFLICT  p_expected_version is NULL or not the current version
--   INVALID_TRANSITION    (current status, p_to_status) not in allowed_transition
--   DIAGNOSIS_REQUIRED    rule needs a diagnosis and it is blank
--   COMMENT_REQUIRED      rule needs a comment and it is blank
-- Result: the updated ticket (read model).
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_change_ticket_status;

DELIMITER $$

CREATE PROCEDURE sp_change_ticket_status(
    IN p_ticket_id         INT,
    IN p_to_status         VARCHAR(20),
    IN p_diagnosis         VARCHAR(1000),
    IN p_comment           VARCHAR(1000),
    IN p_actor             VARCHAR(100),
    IN p_expected_version  INT
)
BEGIN
    DECLARE v_from_status        VARCHAR(20)   DEFAULT NULL;
    DECLARE v_version            INT           DEFAULT NULL;
    DECLARE v_to_status          VARCHAR(20)   DEFAULT NULL;
    DECLARE v_requires_diagnosis TINYINT(1)    DEFAULT NULL;
    DECLARE v_requires_comment   TINYINT(1)    DEFAULT NULL;
    DECLARE v_diagnosis          VARCHAR(1000) DEFAULT NULL;
    DECLARE v_comment            VARCHAR(1000) DEFAULT NULL;
    DECLARE v_history_comment    VARCHAR(1000) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_to_status = NULLIF(TRIM(p_to_status), '');
    SET v_diagnosis = NULLIF(TRIM(p_diagnosis), '');
    SET v_comment   = NULLIF(TRIM(p_comment), '');

    START TRANSACTION;

    -- No row leaves both variables NULL (NOT FOUND is a warning, not an error).
    SELECT status, version
      INTO v_from_status, v_version
      FROM ticket
     WHERE id = p_ticket_id
       FOR UPDATE;

    IF v_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TICKET_NOT_FOUND';
    END IF;

    IF p_expected_version IS NULL OR v_version <> p_expected_version THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CONCURRENCY_CONFLICT';
    END IF;

    SELECT requires_diagnosis, requires_comment
      INTO v_requires_diagnosis, v_requires_comment
      FROM allowed_transition
     WHERE from_status = v_from_status
       AND to_status = v_to_status;

    IF v_requires_diagnosis IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_TRANSITION';
    END IF;

    IF v_requires_diagnosis = 1 AND v_diagnosis IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'DIAGNOSIS_REQUIRED';
    END IF;

    IF v_requires_comment = 1 AND v_comment IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'COMMENT_REQUIRED';
    END IF;

    UPDATE ticket
       SET status    = v_to_status,
           diagnosis = COALESCE(v_diagnosis, diagnosis),
           version   = version + 1
     WHERE id = p_ticket_id;

    -- LEFT keeps "Diagnosis: " + a 1000-char diagnosis inside VARCHAR(1000).
    SET v_history_comment = COALESCE(
        v_comment,
        LEFT(CONCAT('Diagnosis: ', v_diagnosis), 1000)
    );

    INSERT INTO ticket_history (ticket_id, event_type, from_status, to_status, comment, actor)
    VALUES (p_ticket_id, 'STATUS_CHANGED', v_from_status, v_to_status,
            v_history_comment, NULLIF(TRIM(p_actor), ''));

    COMMIT;

    SELECT t.id, t.title, t.description, t.asset_code, t.priority, t.status,
           t.diagnosis, t.assigned_operator_id, o.name AS assigned_operator_name,
           t.reported_by, t.created_at, t.updated_at, t.version
      FROM ticket t
      LEFT JOIN operator o ON o.id = t.assigned_operator_id
     WHERE t.id = p_ticket_id;
END$$

DELIMITER ;

-- -----------------------------------------------------------------------------
-- sp_add_comment
-- Adds a COMMENT event to a ticket. Does not change the ticket or its version.
-- Errors (checked in this order):
--   TICKET_NOT_FOUND  no ticket with p_ticket_id
--   COMMENT_EMPTY     comment is blank
-- Result: the inserted history row.
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_add_comment;

DELIMITER $$

CREATE PROCEDURE sp_add_comment(
    IN p_ticket_id  INT,
    IN p_comment    VARCHAR(1000),
    IN p_actor      VARCHAR(100)
)
BEGIN
    DECLARE v_ticket_id  INT           DEFAULT NULL;
    DECLARE v_comment    VARCHAR(1000) DEFAULT NULL;
    DECLARE v_history_id BIGINT        DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_comment = NULLIF(TRIM(p_comment), '');

    START TRANSACTION;

    SELECT id
      INTO v_ticket_id
      FROM ticket
     WHERE id = p_ticket_id
       FOR SHARE;

    IF v_ticket_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TICKET_NOT_FOUND';
    END IF;

    IF v_comment IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'COMMENT_EMPTY';
    END IF;

    INSERT INTO ticket_history (ticket_id, event_type, from_status, to_status, comment, actor)
    VALUES (v_ticket_id, 'COMMENT', NULL, NULL, v_comment, NULLIF(TRIM(p_actor), ''));

    SET v_history_id = LAST_INSERT_ID();

    COMMIT;

    SELECT h.id, h.ticket_id, h.event_type, h.from_status, h.to_status,
           h.comment, h.actor, h.created_at
      FROM ticket_history h
     WHERE h.id = v_history_id;
END$$

DELIMITER ;

-- -----------------------------------------------------------------------------
-- sp_assign_ticket
-- Assigns a ticket to an operator, or unassigns it when p_operator_id is NULL.
-- Locks the ticket row (FOR UPDATE) and increments version.
-- History comment = "Assigned to <operator name>" or "Unassigned".
-- Errors (checked in this order):
--   TICKET_NOT_FOUND      no ticket with p_ticket_id
--   OPERATOR_NOT_FOUND    p_operator_id is not NULL and no such operator
--   CONCURRENCY_CONFLICT  p_expected_version is NULL or not the current version
-- Result: the updated ticket (read model).
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_assign_ticket;

DELIMITER $$

CREATE PROCEDURE sp_assign_ticket(
    IN p_ticket_id         INT,
    IN p_operator_id       INT,
    IN p_actor             VARCHAR(100),
    IN p_expected_version  INT
)
BEGIN
    DECLARE v_version       INT          DEFAULT NULL;
    DECLARE v_operator_name VARCHAR(100) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT version
      INTO v_version
      FROM ticket
     WHERE id = p_ticket_id
       FOR UPDATE;

    IF v_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TICKET_NOT_FOUND';
    END IF;

    IF p_operator_id IS NOT NULL THEN
        SELECT name
          INTO v_operator_name
          FROM operator
         WHERE id = p_operator_id
           FOR SHARE;

        IF v_operator_name IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OPERATOR_NOT_FOUND';
        END IF;
    END IF;

    IF p_expected_version IS NULL OR v_version <> p_expected_version THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CONCURRENCY_CONFLICT';
    END IF;

    UPDATE ticket
       SET assigned_operator_id = p_operator_id,
           version              = version + 1
     WHERE id = p_ticket_id;

    INSERT INTO ticket_history (ticket_id, event_type, from_status, to_status, comment, actor)
    VALUES (p_ticket_id, 'ASSIGNED', NULL, NULL,
            IF(p_operator_id IS NULL, 'Unassigned', CONCAT('Assigned to ', v_operator_name)),
            NULLIF(TRIM(p_actor), ''));

    COMMIT;

    SELECT t.id, t.title, t.description, t.asset_code, t.priority, t.status,
           t.diagnosis, t.assigned_operator_id, o.name AS assigned_operator_name,
           t.reported_by, t.created_at, t.updated_at, t.version
      FROM ticket t
      LEFT JOIN operator o ON o.id = t.assigned_operator_id
     WHERE t.id = p_ticket_id;
END$$

DELIMITER ;
