# Cross-Service Integrity Design

## Overview

This document addresses ForeignKeyViolation errors that occur when deleting Users, Agents, or Properties in the main Django backend. The issue arises because the AI backend service has models (AIReport, ChatSession, ChatMessage) that reference User and Property tables in a shared database. When these entities are deleted, the cascade deletion fails due to foreign key constraints from the AI backend models, which are not visible to the main backend's ORM.

The fix will implement shadow models in the main backend to represent the AI backend's models and add pre-deletion cleanup logic in the ViewSet destroy methods to ensure referential integrity across both services before deletion occurs.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when a User, Agent, or Property with associated AI backend records (AIReport, ChatSession, ChatMessage) is deleted through the main backend ViewSets
- **Property (P)**: The desired behavior - all AI backend records should be deleted in the correct dependency order before the main entity is deleted
- **Preservation**: Existing deletion behavior for entities without AI backend references must remain unchanged
- **Shadow Models**: Unmanaged Django models in the main backend that mirror the AI backend's models, allowing the main backend's ORM to query and delete AI backend records
- **UserViewSet**: The ViewSet in `backend/auth_api/views.py` that handles User CRUD operations
- **AgentViewSet**: The ViewSet in `backend/auth_api/views.py` that handles Agent CRUD operations
- **PropertyViewSet**: The ViewSet in `backend/property_api/views.py` that handles Property CRUD operations
- **Dependency Chain**: The cascade relationship order: ChatMessage → ChatSession → AIReport → (Property/User)

## Bug Details

### Bug Condition

The bug manifests when a User, Agent, or Property with associated AI backend records is deleted through the main backend ViewSets. The main backend's ORM is unaware of the AI backend's foreign key constraints, causing database-level ForeignKeyViolation errors when attempting to delete entities that have references from AIReport, ChatSession, or ChatMessage tables.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type DeleteRequest containing entity_type and entity_id
  OUTPUT: boolean
  
  RETURN (input.entity_type == "User" AND hasAIBackendReferences(input.entity_id, "User"))
         OR (input.entity_type == "Agent" AND hasAIBackendReferences(input.entity_id, "Agent"))
         OR (input.entity_type == "Property" AND hasAIBackendReferences(input.entity_id, "Property"))
         
WHERE hasAIBackendReferences(entity_id, entity_type) IS:
  IF entity_type == "User" THEN
    RETURN AIReport.objects.filter(user_id=entity_id).exists()
           OR ChatSession.objects.filter(user_id=entity_id).exists()
  ELSE IF entity_type == "Agent" THEN
    property_ids = Property.objects.filter(agent_id=entity_id).values_list('id', flat=True)
    RETURN AIReport.objects.filter(property_id__in=property_ids).exists()
  ELSE IF entity_type == "Property" THEN
    RETURN AIReport.objects.filter(property_id=entity_id).exists()
  END IF
END FUNCTION
```

### Examples

- **User Deletion with AIReport**: User ID 5 has 3 AIReport records. Attempting to delete User 5 raises ForeignKeyViolation due to AIReport.user foreign key constraint.
- **User Deletion with ChatSession**: User ID 7 has 2 ChatSession records (each with multiple ChatMessage records). Attempting to delete User 7 raises ForeignKeyViolation due to ChatSession.user foreign key constraint.
- **Agent Deletion with Property AIReports**: Agent ID 3 owns 5 Properties, 2 of which have AIReport records. Attempting to delete Agent 3 raises ForeignKeyViolation due to AIReport.property foreign key constraint on the agent's properties.
- **Property Deletion with AIReport Chain**: Property ID 10 has 1 AIReport with 2 ChatSession records (each with 5 ChatMessage records). Attempting to delete Property 10 raises ForeignKeyViolation due to the cascading relationship chain.

## Expected Behavior

The fix will ensure that when Users, Agents, or Properties with AI backend references are deleted, all AI backend records are cleaned up in the correct dependency order (ChatMessage → ChatSession → AIReport) before the main entity deletion proceeds. This will prevent ForeignKeyViolation errors.

Existing deletion behavior for entities without AI backend references will remain unchanged, as validated by existing test suites in auth_api and property_api.

## Hypothesized Root Cause

Based on the bug description and codebase analysis, the root cause is:

1. **ORM Visibility Gap**: The main backend's Django ORM is unaware of the AI backend's models (AIReport, ChatSession, ChatMessage) because they exist in a separate Django project (backend_ai) that shares the same database. The main backend has no model definitions for these tables.

2. **Missing Cascade Handling**: When the main backend attempts to delete a User, Agent, or Property, Django's ORM only handles cascades for relationships it knows about (Agent → User, Property → Agent). It does not handle the AI backend's foreign key constraints.

3. **Database-Level Constraint Enforcement**: The database enforces the foreign key constraints from the AI backend tables, causing ForeignKeyViolation errors when the main backend tries to delete referenced entities.

4. **No Pre-Deletion Cleanup**: The ViewSet destroy methods (UserViewSet.destroy, AgentViewSet.destroy, PropertyViewSet.destroy) do not include any logic to clean up AI backend records before deletion.

## Correctness Properties

Property 1: Bug Condition - AI Backend Records Cleanup

_For any_ deletion request where the entity (User, Agent, or Property) has associated AI backend records (AIReport, ChatSession, ChatMessage), the fixed destroy methods SHALL delete all AI backend records in the correct dependency order (ChatMessage → ChatSession → AIReport) before proceeding with the main entity deletion, ensuring no ForeignKeyViolation errors occur.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

**Note**: Preservation of existing deletion behavior for entities without AI backend references is already validated by existing test suites in auth_api and property_api (Requirements 3.1-3.10).

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File 1**: `backend/core_db/models.py`

**Changes**: Add shadow models for AI backend tables

**Specific Changes**:
1. **Add AIReport Shadow Model**: Create an unmanaged Django model that mirrors the AI backend's AIReport model
   - Include foreign keys to User and Property
   - Set `managed = False` to prevent migrations
   - Set correct `db_table` name to match AI backend table

2. **Add ChatSession Shadow Model**: Create an unmanaged Django model that mirrors the AI backend's ChatSession model
   - Include foreign keys to User and AIReport
   - Set `managed = False` to prevent migrations
   - Set correct `db_table` name to match AI backend table

3. **Add ChatMessage Shadow Model**: Create an unmanaged Django model that mirrors the AI backend's ChatMessage model
   - Include foreign key to ChatSession
   - Set `managed = False` to prevent migrations
   - Set correct `db_table` name to match AI backend table

**File 2**: `backend/auth_api/views.py`

**Function**: `UserViewSet.destroy`

**Specific Changes**:
1. **Import Shadow Models**: Add imports for AIReport, ChatSession, ChatMessage from core_db.models

2. **Add Pre-Deletion Cleanup**: Before calling `super().destroy()`, add logic to:
   - Query for AIReport records where user_id matches the user being deleted
   - For each AIReport, delete associated ChatSession records (which will cascade to ChatMessage via Django ORM)
   - Delete the AIReport records
   - Query for ChatSession records where user_id matches the user being deleted (sessions not linked to reports)
   - Delete these ChatSession records (which will cascade to ChatMessage via Django ORM)

3. **Maintain Existing Logic**: Ensure all existing permission checks, superuser validation, and response formatting remain unchanged

**File 3**: `backend/auth_api/views.py`

**Function**: `AgentViewSet.destroy`

**Specific Changes**:
1. **Import Shadow Models**: Add imports for AIReport, ChatSession, ChatMessage from core_db.models

2. **Add Pre-Deletion Cleanup**: Before calling `super().destroy()`, add logic to:
   - Get all Property IDs owned by the Agent being deleted
   - Query for AIReport records where property_id is in the list of Property IDs
   - For each AIReport, delete associated ChatSession records (which will cascade to ChatMessage via Django ORM)
   - Delete the AIReport records

3. **Maintain Existing Logic**: Ensure all existing permission checks, image cleanup, and response formatting remain unchanged

**File 4**: `backend/property_api/views.py`

**Function**: `PropertyViewSet.destroy`

**Specific Changes**:
1. **Import Shadow Models**: Add imports for AIReport, ChatSession, ChatMessage from core_db.models

2. **Add Pre-Deletion Cleanup**: Before calling `super().destroy()`, add logic to:
   - Query for AIReport records where property_id matches the Property being deleted
   - For each AIReport, delete associated ChatSession records (which will cascade to ChatMessage via Django ORM)
   - Delete the AIReport records

3. **Maintain Existing Logic**: Ensure all existing permission checks, image cleanup, and response formatting remain unchanged

## Testing Strategy

### Validation Approach

The testing strategy focuses on surfacing counterexamples that demonstrate the bug on unfixed code, then verifying the fix works correctly. Existing test suites in auth_api and property_api already validate that deletion behavior for entities without AI backend references works correctly.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Create test scenarios with Users, Agents, and Properties that have AI backend references, then attempt to delete them using the unfixed ViewSet destroy methods. Run these tests on the UNFIXED code to observe ForeignKeyViolation errors and confirm the root cause.

**Test Cases**:
1. **User with AIReport Deletion**: Create a User with AIReport records, attempt deletion (will fail on unfixed code with ForeignKeyViolation)
2. **User with ChatSession Deletion**: Create a User with ChatSession records, attempt deletion (will fail on unfixed code with ForeignKeyViolation)
3. **Agent with Property AIReports Deletion**: Create an Agent with Properties that have AIReport records, attempt deletion (will fail on unfixed code with ForeignKeyViolation)
4. **Property with AIReport Chain Deletion**: Create a Property with AIReport, ChatSession, and ChatMessage records, attempt deletion (will fail on unfixed code with ForeignKeyViolation)

**Expected Counterexamples**:
- ForeignKeyViolation errors when attempting to delete entities with AI backend references
- Error messages indicating constraint violations on ai_report.user_id, ai_report.property_id, or chat_session.user_id

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL deletion_request WHERE isBugCondition(deletion_request) DO
  result := destroy_fixed(deletion_request)
  ASSERT result.status_code == 200
  ASSERT entity_deleted(deletion_request.entity_id)
  ASSERT no_ai_backend_references_remain(deletion_request.entity_id)
END FOR
```

### Unit Tests

- Test User deletion with AIReport records only
- Test User deletion with ChatSession records only
- Test User deletion with both AIReport and ChatSession records
- Test Agent deletion with Properties that have AIReport records
- Test Property deletion with AIReport, ChatSession, and ChatMessage chain

### Integration Tests

- Test full deletion flow for User with multiple AIReport and ChatSession records
- Test full deletion flow for Agent with multiple Properties, each with AI backend references
- Test full deletion flow for Property with complex ChatMessage → ChatSession → AIReport chain
