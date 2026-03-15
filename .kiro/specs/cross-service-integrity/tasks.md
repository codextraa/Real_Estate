# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - AI Backend Records Cleanup
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: Users/Agents/Properties with AI backend references
  - Test that deletion requests for entities with AI backend references (AIReport, ChatSession, ChatMessage) complete successfully without ForeignKeyViolation errors
  - The test assertions should verify: (1) deletion completes with status 200, (2) entity is deleted, (3) all AI backend references are cleaned up
  - Test cases to include:
    - User with AIReport records deletion
    - User with ChatSession records deletion
    - Agent with Properties that have AIReport records deletion
    - Property with AIReport, ChatSession, and ChatMessage chain deletion
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS with ImportError (shadow models don't exist in core_db.models yet - this is correct and proves the test setup is working)
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Add shadow models for AI backend tables
  - Create AIReport shadow model in `backend/core_db/models.py`
    - Include foreign keys to User and Property
    - Set `managed = False` to prevent migrations
    - Set correct `db_table` name to match AI backend table
  - Create ChatSession shadow model in `backend/core_db/models.py`
    - Include foreign keys to User and AIReport
    - Set `managed = False` to prevent migrations
    - Set correct `db_table` name to match AI backend table
  - Create ChatMessage shadow model in `backend/core_db/models.py`
    - Include foreign key to ChatSession
    - Set `managed = False` to prevent migrations
    - Set correct `db_table` name to match AI backend table
  - _Bug_Condition: isBugCondition(input) where entity has AI backend references (AIReport, ChatSession, ChatMessage)_
  - _Expected_Behavior: Shadow models allow main backend ORM to query and delete AI backend records_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Fix for cross-service integrity bug

  - [x] 3.1 Implement UserViewSet.destroy pre-deletion cleanup
    - Import shadow models (AIReport, ChatSession, ChatMessage) from core_db.models
    - Add pre-deletion cleanup logic before `super().destroy()`:
      - Query for AIReport records where user_id matches the user being deleted
      - For each AIReport, delete associated ChatSession records (cascades to ChatMessage)
      - Delete the AIReport records
      - Query for ChatSession records where user_id matches (sessions not linked to reports)
      - Delete these ChatSession records (cascades to ChatMessage)
    - Maintain all existing permission checks, superuser validation, and response formatting
    - _Bug_Condition: isBugCondition(input) where input.entity_type == "User" AND hasAIBackendReferences(input.entity_id, "User")_
    - _Expected_Behavior: All AI backend records deleted in correct dependency order before User deletion_
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Implement AgentViewSet.destroy pre-deletion cleanup
    - Import shadow models (AIReport, ChatSession, ChatMessage) from core_db.models
    - Add pre-deletion cleanup logic before `super().destroy()`:
      - Get all Property IDs owned by the Agent being deleted
      - Query for AIReport records where property_id is in the list of Property IDs
      - For each AIReport, delete associated ChatSession records (cascades to ChatMessage)
      - Delete the AIReport records
    - Maintain all existing permission checks, image cleanup, and response formatting
    - _Bug_Condition: isBugCondition(input) where input.entity_type == "Agent" AND hasAIBackendReferences(input.entity_id, "Agent")_
    - _Expected_Behavior: All AI backend records for Agent's Properties deleted in correct dependency order before Agent deletion_
    - _Requirements: 2.3, 2.4_

  - [x] 3.3 Implement PropertyViewSet.destroy pre-deletion cleanup
    - Import shadow models (AIReport, ChatSession, ChatMessage) from core_db.models
    - Add pre-deletion cleanup logic before `super().destroy()`:
      - Query for AIReport records where property_id matches the Property being deleted
      - For each AIReport, delete associated ChatSession records (cascades to ChatMessage)
      - Delete the AIReport records
    - Maintain all existing permission checks, image cleanup, and response formatting
    - _Bug_Condition: isBugCondition(input) where input.entity_type == "Property" AND hasAIBackendReferences(input.entity_id, "Property")_
    - _Expected_Behavior: All AI backend records deleted in correct dependency order before Property deletion_
    - _Requirements: 2.5_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - AI Backend Records Cleanup
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify all deletion scenarios complete successfully without ForeignKeyViolation errors
    - Verify all AI backend records are cleaned up correctly
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
