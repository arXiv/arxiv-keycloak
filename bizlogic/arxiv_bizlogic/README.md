# arXiv Bizlogic - Tapir Audit Events

This module provides an interface to generating audit event records.


## Overview

The audit event system consists of:
- `AdminAuditActionEnum`: Enumeration of available admin actions
- `AdminAuditEvent`: Base class for all audit events
- Specialized audit event classes for different types of actions
- Database persistence through `TapirAdminAudit` model

## Core Classes

### AdminAuditActionEnum
Enumeration defining all possible administrative actions that can be audited:
- `ADD_COMMENT`, `ADD_PAPER_OWNER`, `CHANGE_EMAIL`, `SUSPEND_USER`, etc.

### AdminAuditEvent (Base Class)
**Constructor**: `__init__(admin_id, affected_user, session_id, remote_ip=None, remote_hostname=None, tracking_cookie=None, comment=None, data=None, timestamp=None)`

Base class for all administrative audit events with common attributes:
- `admin_id`: ID of administrator performing the action
- `affected_user`: ID of user being affected
- `session_id`: TAPIR session ID
- `remote_ip`: Administrator's IP address (optional)
- `remote_hostname`: Administrator's hostname (optional)
- `tracking_cookie`: Session tracking cookie (optional)
- `comment`: Optional comment about the action
- `data`: Additional action-specific data (optional)
- `timestamp`: Unix timestamp (auto-generated if not provided)

## Paper-Related Events

### AdminAudit_PaperEvent (Base Class)
**Constructor**: Inherits from `AdminAuditEvent` but expects `paper_id` parameter instead of `data`
paper_id is aka arXiv ID (yymm.nnnnnn for example)

Base class for paper-related audit events.

### AdminAudit_AddPaperOwner
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs when an admin adds a paper owner.

### AdminAudit_AddPaperOwner2
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs when an admin adds a paper owner through the process-ownership screen.

### AdminAudit_ChangePaperPassword
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs when an admin changes a paper's password.

### AdminAudit_AdminChangePaperPassword
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs admin-level paper password changes.

### AdminAudit_AdminMakeAuthor
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs when an admin makes a user an author of a paper.

### AdminAudit_AdminMakeNonauthor
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs when an admin removes a user's authorship.

### AdminAudit_AdminRevokePaperOwner
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs when an admin revokes paper ownership.

### AdminAudit_AdminUnrevokePaperOwner
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs when an admin restores paper ownership.

### AdminAudit_AdminNotArxivRevokePaperOwner
**Constructor**: Same as `AdminAudit_PaperEvent`
Logs paper ownership revocation (non-arXiv specific).

## User Account Events

### AdminAudit_AddComment
**Constructor**: Same as `AdminAuditEvent`
Logs when an admin adds a comment about a user.

### AdminAudit_BecomeUser
**Constructor**: Inherits from `AdminAuditEvent` but expects `new_session_id` parameter instead of `data`
Logs when an admin impersonates another user.

### AdminAudit_ChangeEmail
**Constructor**: Inherits from `AdminAuditEvent` but expects `email` parameter instead of `data`
Logs when an admin changes a user's email address.

### AdminAudit_ChangePassword
**Constructor**: Same as `AdminAuditEvent`
Logs when an admin changes a user's password.

### AdminAudit_SuspendUser
**Constructor**: Same as `AdminAuditEvent` (automatically sets banned flag data)
Logs when an admin suspends a user account.

### AdminAudit_UnuspendUser
**Constructor**: Same as `AdminAuditEvent` (automatically sets unbanned flag data)
Logs when an admin removes a user's suspension.

### AdminAudit_ChangeStatus
**Constructor**: Inherits from `AdminAuditEvent` but expects `status_before` and `status_after` parameters instead of `data`
Logs when an admin changes a user's veto status.

## Endorsement Events

### AdminAudit_EndorseEvent (Base Class)
**Constructor**: Inherits from `AdminAuditEvent` but expects `endorser`, `endorsee`, and `category` parameters instead of `data`

Base class for endorsement-related events.

### AdminAudit_EndorsedBySuspect
**Constructor**: Same as `AdminAudit_EndorseEvent`
Logs when a user is endorsed by a suspect user.

### AdminAudit_GotNegativeEndorsement
**Constructor**: Same as `AdminAudit_EndorseEvent`
Logs when a user receives a negative endorsement.

## Moderator Events

### AdminAudit_MakeModerator
**Constructor**: Inherits from `AdminAuditEvent` but expects `category` parameter instead of `data`
Logs when an admin grants moderator privileges for a category.

### AdminAudit_UnmakeModerator
**Constructor**: Inherits from `AdminAuditEvent` but expects `category` parameter instead of `data`
Logs when an admin revokes moderator privileges for a category.

## Flag Management Events

### AdminAudit_SetFlag (Base Class)
**Constructor**: Abstract base class - not instantiated directly
Base class for flag modification events.

### Flag-Specific Classes
All inherit from `AdminAudit_SetFlag` with specific constructors:

- **AdminAudit_SetGroupTest**: Constructor expects `group_test` (bool)
- **AdminAudit_SetProxy**: Constructor expects `proxy` (bool)
- **AdminAudit_SetSuspect**: Constructor expects `suspect` (bool)
- **AdminAudit_SetXml**: Constructor expects `xml` (bool)
- **AdminAudit_SetEndorsementValid**: Constructor expects `endorsement_valid` (bool)
- **AdminAudit_SetPointValue**: Constructor expects `point_value` (int)
- **AdminAudit_SetEndorsementRequestsValid**: Constructor expects `endorsement_requests_valid` (bool)
- **AdminAudit_SetEmailBouncing**: Constructor expects `email_bouncing` (bool)
- **AdminAudit_SetBanned**: Constructor expects `banned` (bool)
- **AdminAudit_SetEditSystem**: Constructor expects `edit_system` (bool)
- **AdminAudit_SetEditUsers**: Constructor expects `edit_users` (bool)
- **AdminAudit_SetEmailVerified**: Constructor expects `verified` (bool)

## Utility Functions

### admin_audit()
Persists an audit event to the database by creating a `TapirAdminAudit` record.

### create_admin_audit_event()
Creates an `AdminAuditEvent` instance from a `TapirAdminAudit` database record (reverse operation).

### admin_audit_flip_flag_instantiator()
Factory function for creating flag-related audit events from database records.

## Usage Pattern

1. Create appropriate audit event instance with required constructor parameters
2. Call `admin_audit()` to persist the event to database
3. Use `create_admin_audit_event()` to reconstruct events from database records

## Testing

Round-trip test is in `tests/test_admin_audit.py`.
