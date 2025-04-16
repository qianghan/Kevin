# Contract Testing for Profiler

This document describes the contract testing approach for the profiler application, ensuring consistent communication between frontend and backend.

## Overview

Contract testing ensures that the API contracts between frontend and backend are well-defined and consistent. This helps catch interface mismatches early and maintains API compatibility.

Our approach includes:
- Shared type definitions
- Schema validation
- Contract test suites
- OpenAPI documentation
- TypeScript client generation

## Shared Type Definitions

Type definitions are shared between frontend and backend in `profiler/app/shared/types.ts`. These types define the structure of WebSocket messages and ensure consistency.

Key types include:
- `WebSocketMessage` - Base interface for all messages
- `ProfileStateMessage` - Profile state updates
- `DocumentAnalysisMessage` - Document analysis requests
- `QuestionMessage` - Question asking
- `RecommendationMessage` - Recommendation requests

## Schema Validation

We use validation on both sides:
- Frontend: Zod schemas in `profiler/app/ui/src/services/validation.ts`
- Backend: Pydantic models in `profiler/app/backend/utils/validation.py`

This ensures messages conform to the expected structure both when sending and receiving.

## Contract Test Suite

Contract tests are in `profiler/tests/ui/__tests__/websocket.contract.test.ts`. These tests verify that:
- Messages follow the expected schema
- Invalid messages are rejected
- Message types are properly handled

## OpenAPI Documentation

The WebSocket API is documented using OpenAPI in `profiler/docs/api/websocket_api.yaml`. This specification:
- Documents the API endpoints
- Defines message schemas
- Provides examples
- Serves as source of truth for client generation

## Integration Tests

Integration tests in `profiler/tests/integration/profile_flow.test.ts` verify the complete flow:
- WebSocket connection
- Message handling
- State updates
- Error handling

## TypeScript Client Generation

The client generator in `profiler/tools/generate_client.py` creates:
- TypeScript interfaces from OpenAPI schema
- A client class for interacting with the API

To generate the client:
```bash
cd profiler
./tools/generate_client.sh
```

This produces:
- `profiler/app/ui/src/api-client/api-interfaces.ts` - TypeScript interfaces
- `profiler/app/ui/src/api-client/api-client.ts` - TypeScript client class

## Best Practices

- Always update the shared type definitions when changing message structure
- Run contract tests when making API changes
- Update the OpenAPI spec when modifying endpoints
- Regenerate the client after API changes
- Write integration tests for new features 