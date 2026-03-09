# Requirements Document

## Introduction

This document addresses ForeignKeyViolation errors that occur when deleting Users, Agents, or Properties in the main Django backend. The issue arises because a separate AI backend service has models (AIReport, ChatSession, ChatMessage) that reference the User and Property tables in a shared database. When these entities are deleted, the cascade deletion fails due to foreign key constraints from the AI backend models, which are not visible to the main backend's ORM.

The fix will implement shadow models in the main backend to represent the AI backend's models and add pre-deletion cleanup logic to ensure referential integrity across both services before deletion occurs.

**Cross-Service Foreign Key Relationships:**
- AIReport → Property (property field)
- AIReport → User (user field)
- ChatSession → User (user field)
- ChatSession → AIReport (report field)
- ChatMessage → ChatSession (session field)

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a User with associated AIReport records is deleted through the UserViewSet destroy method THEN the system raises a ForeignKeyViolation error due to AIReport.user foreign key constraint

1.2 WHEN a User with associated ChatSession records is deleted through the UserViewSet destroy method THEN the system raises a ForeignKeyViolation error due to ChatSession.user foreign key constraint

1.3 WHEN an Agent with associated Properties that have AIReport records is deleted through the AgentViewSet destroy method THEN the system raises a ForeignKeyViolation error due to AIReport.property foreign key constraint

1.4 WHEN a Property with associated AIReport records is deleted through the PropertyViewSet destroy method THEN the system raises a ForeignKeyViolation error due to AIReport.property foreign key constraint

1.5 WHEN a Property deletion is attempted and the Property has AIReport records with ChatSession records THEN the system raises a ForeignKeyViolation error due to the cascading relationship chain (ChatMessage → ChatSession → AIReport → Property)

### Expected Behavior (Correct)

2.1 WHEN a User with associated AIReport records is deleted through the UserViewSet destroy method THEN the system SHALL first delete all AIReport records (and their cascading ChatSession and ChatMessage records) associated with that User before proceeding with the User deletion

2.2 WHEN a User with associated ChatSession records is deleted through the UserViewSet destroy method THEN the system SHALL first delete all ChatSession records (and their cascading ChatMessage records) associated with that User before proceeding with the User deletion

2.3 WHEN an Agent with associated Properties that have AIReport records is deleted through the AgentViewSet destroy method THEN the system SHALL first delete all AIReport records (and their cascading ChatSession and ChatMessage records) for all Properties owned by that Agent before proceeding with the Agent deletion

2.4 WHEN a Property with associated AIReport records is deleted through the PropertyViewSet destroy method THEN the system SHALL first delete all AIReport records (and their cascading ChatSession and ChatMessage records) associated with that Property before proceeding with the Property deletion

2.5 WHEN any deletion involves AI backend references THEN the system SHALL delete records in the correct dependency order: ChatMessage → ChatSession → AIReport → (Property/User) to maintain referential integrity

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a User with no associated AIReport or ChatSession records is deleted THEN the system SHALL CONTINUE TO delete the User successfully without errors

3.2 WHEN an Agent with no associated Properties is deleted THEN the system SHALL CONTINUE TO delete the Agent and User successfully without errors

3.3 WHEN an Agent with Properties that have no AI backend references is deleted THEN the system SHALL CONTINUE TO delete the Agent, Properties, and User successfully through normal cascade deletion

3.4 WHEN a Property with no associated AIReport records is deleted THEN the system SHALL CONTINUE TO delete the Property successfully through normal cascade deletion

3.5 WHEN a non-superuser attempts to delete another user's User profile THEN the system SHALL CONTINUE TO return a 403 Forbidden error

3.6 WHEN a non-superuser attempts to delete another user's Agent profile THEN the system SHALL CONTINUE TO return a 403 Forbidden error

3.7 WHEN a non-agent attempts to delete a Property they don't own THEN the system SHALL CONTINUE TO return a 403 Forbidden error

3.8 WHEN an Agent is deleted successfully THEN the system SHALL CONTINUE TO delete the associated profile image file (if not the default image) and return a 200 OK response with success message

3.9 WHEN a Property is deleted successfully THEN the system SHALL CONTINUE TO delete the associated property image file (if not the default image) and return a 200 OK response with success message

3.10 WHEN a User attempts to delete a superuser account THEN the system SHALL CONTINUE TO return a 403 Forbidden error with message "You cannot delete superusers"
