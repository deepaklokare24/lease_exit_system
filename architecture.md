# Architecture Diagram for Lease Exit System

{toc:printable=true|style=square|maxLevel=3|type=list|outline=true|include=.*}

{panel:title=Overview|borderStyle=solid|borderColor=#ccc|titleBGColor=#f0f0f0|bgColor=#fff}
This document provides a detailed architecture diagram for the Lease Exit System, including implementation guidelines for Confluence integration.
{panel}

## Diagram Components and Structure

{info:title=Diagram Creation Tools}
* **Confluence Diagram Macro**: Built into Confluence, accessible via the "+" menu
* **Draw.io for Confluence**: More powerful diagramming tool with Confluence integration
* **Lucidchart**: Another option with Confluence integration
* **Mermaid**: Text-based diagramming that works in some Confluence instances
{info}

## System Architecture Components

{panel:title=Component Layers|borderStyle=solid|borderColor=#ccc|titleBGColor=#f0f0f0|bgColor=#fff}
### 1. Client Layer
* Web Browser
* Mobile App (if applicable)

### 2. Frontend Layer
* React Application
* Material UI Components
* Dynamic Form Renderer
* Workflow Visualization

### 3. API Layer
* FastAPI Server
* API Routes (Workflow, Forms, Approvals, Notifications)
* Authentication & Authorization

### 4. Business Logic Layer
* AI Agent Orchestration
* Workflow Engine
* Task Management
* Form Processing

### 5. Data Access Layer
* MongoDB Connection
* Data Models
* Query Services

### 6. Background Processing Layer
* Celery Workers
* Redis Queue
* Scheduled Tasks

### 7. External Services
* Email Service
* OpenAI API
* Document Storage
{panel}

## Component Relationships

{code:title=Architecture Diagram|theme=monospace}

┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
│                                                                         │
│  ┌───────────────────────┐            ┌───────────────────────┐         │
│  │     Web Browser       │            │      Mobile App       │         │
│  └───────────┬───────────┘            └───────────┬───────────┘         │
└──────────────┼────────────────────────────────────┼─────────────────────┘
               │                                    │
               ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      React Application                             │  │
│  │                                                                    │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │  │
│  │  │  Dynamic Form  │  │   Workflow     │  │  Document          │   │  │
│  │  │  Renderer      │  │   Visualization│  │  Management        │   │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘   │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────────┬┼─────────────────────────────────────┘
                                  ││
                                  ▼▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             API LAYER                                    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        FastAPI Server                              │  │
│  │                                                                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │  │
│  │  │  Workflow  │  │   Forms    │  │  Approval  │  │Notification│   │  │
│  │  │  Routes    │  │   Routes   │  │  Routes    │  │  Routes    │   │  │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘   │  │
│  └──────────┼──────────────┼──────────────┼──────────────┼───────────┘  │
└──────────────┼──────────────┼──────────────┼──────────────┼───────────────┘
               │              │              │              │
               ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       BUSINESS LOGIC LAYER                               │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        Crew AI Framework                            │ │
│  │                                                                     │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │ │
│  │  │  Workflow  │  │   Form     │  │  Approval  │  │Notification│    │ │
│  │  │  Designer  │  │   Creator  │  │  Architect │  │ Specialist │    │ │
│  │  │   Agent    │  │   Agent    │  │   Agent    │  │   Agent    │    │ │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘    │ │
│  └──────────┼──────────────┼──────────────┼──────────────┼────────────┘ │
│             │              │              │              │              │
│  ┌──────────┼──────────────┼──────────────┼──────────────┼────────────┐ │
│  │                         Task Management                             │ │
│  │                                                                     │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │ │
│  │  │  Workflow  │  │   Form     │  │  Approval  │  │Notification│    │ │
│  │  │   Tasks    │  │   Tasks    │  │   Tasks    │  │   Tasks    │    │ │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘    │ │
│  └──────────┼──────────────┼──────────────┼──────────────┼────────────┘ │
└──────────────┼──────────────┼──────────────┼──────────────┼──────────────┘
               │              │              │              │
               ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA ACCESS LAYER                                 │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      Database Connection                            │ │
│  │                                                                     │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │ │
│  │  │ LeaseExit  │  │   Form     │  │  Approval  │  │Notification│    │ │
│  │  │   Model    │  │   Model    │  │   Model    │  │   Model    │    │ │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │ │
│  └────────────────────────────┬─────────────────────────────────────────┘ │
└──────────────────────────────┬┼──────────────────────────────────────────┘
                              ││
                              ▼▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKGROUND PROCESSING                               │
│                                                                         │
│  ┌────────────────────┐    ┌────────────────────┐                       │
│  │   Celery Workers   │◄──►│    Redis Queue     │                       │
│  └────────────────────┘    └────────────────────┘                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
               │                                    │
               ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                  │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐    │
│  │  Email Server  │  │   OpenAI API   │  │  Document Storage      │    │
│  └────────────────┘  └────────────────┘  └────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

{code}

## Implementation Options

{panel:title=Implementation Methods|borderStyle=dashed|borderColor=#ccc|titleBGColor=#f7f7f7|bgColor=#fff}
### Option 1: Using Confluence Diagram Macro
1. Edit your Confluence page
2. Click the "+" button to insert a macro
3. Search for "Diagram" and select it
4. Use the diagram editor to create the architecture diagram
5. Save the diagram and it will be embedded in your page

### Option 2: Using Draw.io for Confluence
1. Install the Draw.io app from the Atlassian Marketplace
2. Edit your Confluence page
3. Click the "+" button to insert a macro
4. Search for "Draw.io" and select it
5. Create a new diagram or import one
6. Design your architecture diagram
7. Save the diagram and it will be embedded in your page

### Option 3: Using Mermaid
{panel}

## Mermaid Diagram Definition

{code:title=Mermaid Implementation|theme=dark}
graph TD
    %% Client Layer
    Browser[Web Browser] --> Frontend
    Mobile[Mobile App] --> Frontend
    
    %% Frontend Layer
    subgraph Frontend[Frontend Layer]
        React[React Application]
        Forms[Dynamic Form Renderer]
        Workflow[Workflow Visualization]
        Documents[Document Management]
    end
    
    %% API Layer
    Frontend --> API
    
    subgraph API[API Layer]
        FastAPI[FastAPI Server]
        WorkflowRoutes[Workflow Routes]
        FormRoutes[Form Routes]
        ApprovalRoutes[Approval Routes]
        NotificationRoutes[Notification Routes]
    end
    
    %% Business Logic Layer
    API --> BusinessLogic
    
    subgraph BusinessLogic[Business Logic Layer]
        subgraph Agents[Crew AI Agents]
            WorkflowAgent[Workflow Designer Agent]
            FormAgent[Form Creator Agent]
            ApprovalAgent[Approval Architect Agent]
            NotificationAgent[Notification Specialist Agent]
        end
        
        subgraph Tasks[Task Management]
            WorkflowTasks[Workflow Tasks]
            FormTasks[Form Tasks]
            ApprovalTasks[Approval Tasks]
            NotificationTasks[Notification Tasks]
        end
    end
    
    %% Data Access Layer
    BusinessLogic --> DataAccess
    
    subgraph DataAccess[Data Access Layer]
        MongoDB[(MongoDB)]
        LeaseExitModel[LeaseExit Model]
        FormModel[Form Model]
        ApprovalModel[Approval Model]
        NotificationModel[Notification Model]
    end
    
    %% Background Processing
    BusinessLogic --> Background
    
    subgraph Background[Background Processing]
        Celery[Celery Workers]
        Redis[(Redis Queue)]
        Celery <--> Redis
    end
    
    %% External Services
    Background --> External
    NotificationAgent --> External
    
    subgraph External[External Services]
        Email[Email Server]
        OpenAI[OpenAI API]
        Storage[Document Storage]
    end
{code}

## Style Guide

{panel:title=Visual Styling|borderStyle=solid|borderColor=#ccc|titleBGColor=#f0f0f0|bgColor=#fff}
### Color Coding
|| Component Type || Color || Usage ||
| Frontend Components | Blue | React components, UI elements |
| API Components | Green | FastAPI endpoints, routes |
| Business Logic Components | Orange | AI agents, workflow engine |
| Data Components | Purple | Database models, connections |
| External Services | Gray | Third-party integrations |

### Connection Types
|| Connection Type || Line Style || Description ||
| Synchronous Calls | Solid | Direct, blocking calls |
| Asynchronous Calls | Dashed | Non-blocking operations |
| Data Flow | Dotted | Data movement between components |
{panel}

## Component Groups

{panel:title=Logical Grouping|borderStyle=dashed|borderColor=#ccc|titleBGColor=#e9f7f2|bgColor=#fff}
### AI Agents Group
* Workflow Designer Agent
* Form Creator Agent
* Approval Architect Agent
* Notification Specialist Agent

### Task Management Group
* Workflow Tasks
* Form Tasks
* Approval Tasks
* Notification Tasks

### Data Models Group
* LeaseExit Model
* Form Model
* Approval Model
* Notification Model
{panel}

## Legend

{status:title=Symbol Legend|subtle=false|colour=grey}
* ▢ Component/Service
* → Synchronous Flow
* ⇢ Asynchronous Flow
* ⇄ Bidirectional Communication
* ⬡ External Service
* ⬢ Database/Storage
{status}

{note:title=Implementation Note}
When implementing this diagram in your Confluence page, ensure that all components are properly aligned and connections are clearly visible. Use the style guide to maintain consistency across different sections of the diagram.
{note}

{panel:title=Best Practices|borderStyle=dashed|borderColor=#ccc|titleBGColor=#e9f7f2|bgColor=#fff}
1. Maintain consistent spacing between components
2. Use appropriate line weights for different connection types
3. Include clear labels for all components
4. Group related components using containers
5. Add tooltips for complex components
6. Ensure the diagram is readable at different zoom levels
{panel}