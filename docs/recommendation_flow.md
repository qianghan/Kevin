# Recommendation Engine Flow Diagrams

This document contains diagrams illustrating the recommendation generation process and architecture.

## Recommendation Generation Process

```mermaid
flowchart TD
    A[User Profile] --> E[Data Collection]
    B[User Documents] --> E
    C[Q&A History] --> E
    D[Peer Profiles] --> E
    
    E --> F[Analysis]
    
    F --> G1[Profile Recommendations]
    F --> G2[Document Recommendations]
    F --> G3[Peer Comparison Recommendations]
    F --> G4[Q&A-Based Recommendations]
    
    G1 --> H[Filtering & Prioritization]
    G2 --> H
    G3 --> H
    G4 --> H
    
    H --> I[Personalized Recommendations]
    
    I --> J[Notification Generation]
    
    J --> K[User Notification]
```

## Recommendation Service Architecture

```mermaid
classDiagram
    class IRecommendationService {
        <<interface>>
        +generate_recommendations_for_user(user_id)
        +get_recommendations_for_user(user_id, status)
        +get_recommendation_by_id(recommendation_id)
        +update_recommendation_status(recommendation_id, status)
        +update_recommendation_progress(recommendation_id, progress)
        +get_recommendation_history(user_id, start_date, end_date)
    }
    
    class RecommendationService {
        -profile_service
        -qa_service
        -document_service
        -notification_service
        -recommendation_repository
        +generate_recommendations_for_user(user_id)
        -_generate_profile_recommendations(profile)
        -_generate_peer_comparison_recommendations(profile)
        -_generate_document_recommendations(user_id)
        -_generate_qa_recommendations(user_id)
        -_filter_duplicate_recommendations(new_recommendations, existing_recommendations)
    }
    
    class IRecommendationRepository {
        <<interface>>
        +save_recommendation(recommendation)
        +get_recommendations_for_user(user_id, status)
        +get_recommendation_by_id(recommendation_id)
        +update_recommendation_status(recommendation_id, status)
        +update_recommendation_progress(recommendation_id, progress)
        +get_recommendation_history(user_id, start_date, end_date)
    }
    
    class InMemoryRecommendationRepository {
        -recommendations
        +save_recommendation(recommendation)
        +get_recommendations_for_user(user_id, status)
        +get_recommendation_by_id(recommendation_id)
        +update_recommendation_status(recommendation_id, status)
        +update_recommendation_progress(recommendation_id, progress)
        +get_recommendation_history(user_id, start_date, end_date)
    }
    
    class SqlAlchemyRecommendationRepository {
        -session_factory
        +save_recommendation(recommendation)
        +get_recommendations_for_user(user_id, status)
        +get_recommendation_by_id(recommendation_id)
        +update_recommendation_status(recommendation_id, status)
        +update_recommendation_progress(recommendation_id, progress)
        +get_recommendation_history(user_id, start_date, end_date)
    }
    
    class Recommendation {
        +id
        +user_id
        +title
        +description
        +category
        +priority
        +steps
        +detailed_steps
        +created_at
        +expires_at
        +completed_at
        +status
        +progress
        +related_entity_id
        +metadata
    }
    
    IRecommendationService <|.. RecommendationService
    IRecommendationRepository <|.. InMemoryRecommendationRepository
    IRecommendationRepository <|.. SqlAlchemyRecommendationRepository
    RecommendationService --> IRecommendationRepository
    InMemoryRecommendationRepository --> Recommendation
    SqlAlchemyRecommendationRepository --> Recommendation
```

## Recommendation API Flow

```mermaid
sequenceDiagram
    actor User
    participant API
    participant Service
    participant Repository
    participant NotificationService
    
    User->>API: GET /recommendations/generate
    API->>Service: generate_recommendations_for_user()
    Service->>Repository: get_recommendations_for_user()
    Repository-->>Service: existing recommendations
    
    Service->>Service: analyze profile
    Service->>Service: analyze documents
    Service->>Service: analyze Q&A history
    Service->>Service: filter recommendations
    
    Service->>Repository: save_recommendation()
    Repository-->>Service: saved recommendations
    
    Service->>NotificationService: create_recommendation_notification()
    NotificationService-->>Service: notification created
    
    Service-->>API: recommendations
    API-->>User: recommendations
    
    User->>API: PATCH /recommendations/{id}/progress
    API->>Service: update_recommendation_progress()
    Service->>Repository: update_recommendation_progress()
    Repository-->>Service: updated recommendation
    Service-->>API: updated recommendation
    API-->>User: updated recommendation
```

## Recommendation Categories and Types

```mermaid
classDiagram
    class RecommendationCategory {
        <<enumeration>>
        SKILL
        EXPERIENCE
        EDUCATION
        DOCUMENT
        PROFILE
        NETWORKING
        CERTIFICATION
        OTHER
    }
    
    class Recommendation {
        +title: string
        +description: string
        +category: RecommendationCategory
        +priority: float
        +steps: string[]
    }
    
    Recommendation --> RecommendationCategory
    
    class ProfileRecommendation {
        "Add more skills"
        "Create a professional summary"
        "Update profile photo"
    }
    
    class DocumentRecommendation {
        "Upload your resume"
        "Improve document formatting"
        "Update outdated information"
    }
    
    class CertificationRecommendation {
        "Get AWS certification"
        "Complete professional course"
        "Earn industry credential"
    }
    
    Recommendation <|-- ProfileRecommendation
    Recommendation <|-- DocumentRecommendation
    Recommendation <|-- CertificationRecommendation
```

These diagrams illustrate the recommendation engine's architecture, data flow, and component relationships. 