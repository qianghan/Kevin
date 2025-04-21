# Recommendation Generation Process Diagrams

This document provides visual representations of the recommendation engine processes.

## Recommendation Generation Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Data Sources   │     │   Analysis &    │     │  Recommendation │     │   Delivery &    │
│                 │────▶│  Personalization│────▶│   Generation    │────▶│    Tracking     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
       │                        │                       │                       │
       ▼                        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ - Profile Data  │     │ - User Context  │     │ - Priority      │     │ - Notifications │
│ - Documents     │     │ - History       │     │   Calculation   │     │ - Progress      │
│ - Q&A Responses │     │ - Algorithms    │     │ - Action Steps  │     │   Tracking      │
│ - User Activity │     │ - Peer Data     │     │ - Deadlines     │     │ - Feedback      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Service Integration Architecture

```
                            ┌─────────────────────┐
                            │                     │
                            │  RecommendationAPI  │
                            │                     │
                            └──────────┬──────────┘
                                       │
                                       ▼
┌─────────────────┐         ┌─────────────────────┐         ┌─────────────────┐
│                 │         │                     │         │                 │
│  ProfileService │◀────────┤ RecommendationService├───────▶│ NotificationSvc │
│                 │         │                     │         │                 │
└────────┬────────┘         └──────────┬──────────┘         └─────────────────┘
         │                             │                              
         │                             │                              
         ▼                             ▼                              
┌─────────────────┐         ┌─────────────────────┐         ┌─────────────────┐
│                 │         │                     │         │                 │
│ DocumentService │◀────────┤  RecommendationRepo ├───────▶│    QAService    │
│                 │         │                     │         │                 │
└─────────────────┘         └─────────────────────┘         └─────────────────┘
```

## Recommendation Lifecycle

```
           ┌───────────┐
           │  Created  │
           └─────┬─────┘
                 │
                 ▼
┌────────────────────────────┐    ┌─────────────┐
│    User Notification       │───▶│   Active    │
└────────────────────────────┘    └──────┬──────┘
                                         │
                                         ▼
                    ┌──────────────────────────────────┐
                    │                                  │
            ┌───────┴───────┐               ┌──────────┴─────────┐
            │               │               │                    │
            ▼               ▼               ▼                    ▼
      ┌──────────┐   ┌────────────┐   ┌─────────┐       ┌───────────────┐
      │ Progress │   │ Snoozed    │   │ Expired │       │ Completed     │
      └────┬─────┘   └──────┬─────┘   └─────────┘       └───────────────┘
           │                │
           │                │
           ▼                ▼
      ┌──────────┐   ┌────────────┐
      │ Updated  │   │ Reactivated│
      └────┬─────┘   └──────┬─────┘
           │                │
           └────────┬───────┘
                    │
                    ▼
             ┌────────────┐
             │ Completed  │
             └────────────┘
```

## Personalization Algorithm Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User Profile   │     │    Algorithm    │     │  Recommendation │
│    Analysis     │────▶│    Selection    │────▶│   Generation    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       │                        │                       │
       ▼                        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ - Skill Gaps    │     │ - Skill-based   │     │ - Priority      │
│ - Experience    │     │ - Career Path   │     │   Assignment    │
│ - Education     │     │ - Education     │     │ - Timeline      │
│ - Career Goals  │     │ - Peer-based    │     │ - Detail Level  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
``` 