# Plan: MCP Server Architecture for AI-Native Data Access

> **📝 NOTE:** This plan is being updated for the simplified roadmap (September 2025). References to Parquet storage will be updated to JSON format per ADR-025. Core MCP architecture remains valid.

**Status:** Planning - Updated for MVP  
**Date:** 2025-01-18 (Updated 2025-09-07)  
**Author:** AI Contributor  
**Scope:** Design and specify the Model Context Protocol (MCP) server architecture for exposing Gold layer basketball data to AI agents

## Executive Summary

This plan outlines the technical architecture for implementing a Model Context Protocol (MCP) server that will serve as the AI-Native Access Layer for the Hoopstat Haus project. The MCP server will expose our processed basketball statistics stored as JSON files in the Gold layer on S3, making this data accessible to AI agents and Large Language Models through a standardized protocol. This approach aligns with AWS best practices for implementing conversational AI for S3 data.

The solution will be implemented as a serverless Python application running on AWS Lambda, fronted by Amazon API Gateway, and secured with API key authentication. The initial implementation will focus on providing player season statistics, with the architecture designed to easily accommodate additional data endpoints as the system matures.

This MCP server represents the core value proposition of the Hoopstat Haus project - transforming raw basketball data into an AI-accessible format that enables powerful analytical capabilities and natural language interactions with basketball statistics.

## High-Level Feature Idea

Create a serverless MCP server that exposes basketball statistics from our Gold layer (JSON files on S3) to AI agents through a standardized protocol. The server will handle authentication, data querying, and response formatting according to MCP specifications, enabling AI agents to seamlessly access and analyze basketball data.

## Goals & Business Value

- **Enable AI-Native Data Access:** Create the foundational infrastructure that makes our basketball data uniquely valuable by providing AI-native access patterns
- **Demonstrate Data Platform Value:** Showcase the end-to-end data pipeline from ingestion to AI consumption 
- **Establish Scalable Architecture:** Build a foundation that can efficiently serve multiple data types and use cases
- **Maintain Cost Effectiveness:** Leverage serverless architecture to ensure costs scale with usage
- **Ensure Security and Compliance:** Implement proper authentication and access controls for data protection
- **Support Developer Experience:** Provide clear, well-documented APIs that enable easy integration

## Epic Breakdown

### Epic 1: MCP Protocol Foundation
**Goal:** Implement the core Model Context Protocol specifications and server framework

#### User Story 1.1: MCP Protocol Implementation
- **As an** AI agent
- **I want** to discover available data resources through MCP protocol
- **So that** I can understand what basketball data is available for analysis
- **Acceptance Criteria:**
  - Implement MCP resource discovery endpoint
  - Return properly formatted resource manifests for available data
  - Support MCP protocol versioning and capability negotiation
  - Provide clear resource descriptions and schemas

#### User Story 1.2: MCP Server Framework Setup
- **As a** developer
- **I want** a standardized MCP server framework
- **So that** I can easily add new data endpoints following MCP patterns
- **Acceptance Criteria:**
  - Create reusable MCP server framework components
  - Implement request/response handling according to MCP specification
  - Add proper error handling and validation
  - Support async processing for large data queries

#### User Story 1.3: MCP Client Testing Infrastructure
- **As a** developer
- **I want** automated testing tools for MCP protocol compliance
- **So that** I can verify the server correctly implements MCP standards
- **Acceptance Criteria:**
  - Create MCP client test suite for protocol validation
  - Implement automated compliance testing in CI/CD
  - Add integration tests with sample AI agent interactions
  - Validate JSON schema compliance for all responses

### Epic 2: AWS Infrastructure Foundation
**Goal:** Establish the AWS serverless infrastructure for hosting the MCP server

#### User Story 2.1: API Gateway Configuration
- **As an** external client
- **I want** to access the MCP server through a reliable, secure HTTP endpoint
- **So that** AI agents can consistently connect to basketball data services
- **Acceptance Criteria:**
  - Deploy API Gateway with proper routing for MCP endpoints
  - Configure CORS for cross-origin access where appropriate
  - Implement request/response validation and transformation
  - Set up CloudWatch logging for API access patterns
  - Configure throttling and rate limiting policies

#### User Story 2.2: Lambda Function Deployment
- **As a** serverless application
- **I want** to run efficiently on AWS Lambda with proper resource allocation
- **So that** MCP requests are processed quickly and cost-effectively
- **Acceptance Criteria:**
  - Deploy Python Lambda function with optimized resource configuration
  - Implement cold start optimization strategies
  - Configure appropriate timeout and memory settings
  - Set up Lambda environment variables for configuration
  - Enable Lambda logging integration with CloudWatch

#### User Story 2.3: IAM Security Configuration
- **As a** security-conscious system
- **I want** proper IAM roles and policies for all AWS resources
- **So that** access is controlled according to least-privilege principles
- **Acceptance Criteria:**
  - Create Lambda execution role with minimal required permissions
  - Configure S3 access policies for Gold layer data reading
  - Set up API Gateway authorization policies
  - Implement cross-service access controls
  - Document security boundary definitions

### Epic 3: Data Access Layer Implementation
**Goal:** Implement efficient querying and processing of Gold layer Parquet data

#### User Story 3.1: S3 Parquet Data Reader
- **As a** Lambda function
- **I want** to efficiently query Parquet files stored in S3
- **So that** I can retrieve basketball statistics for MCP responses
- **Acceptance Criteria:**
  - Implement AWS Data Wrangler integration for Parquet reading
  - Support filtered queries to minimize data transfer
  - Cache frequently accessed data appropriately
  - Handle partitioned data structures efficiently
  - Implement proper error handling for missing or corrupted data

#### User Story 3.2: Data Query Optimization
- **As a** performance-conscious system
- **I want** optimized data access patterns
- **So that** MCP responses are fast and cost-effective
- **Acceptance Criteria:**
  - Implement columnar query strategies for Parquet files
  - Use S3 Select for server-side filtering where applicable
  - Cache data schemas and metadata
  - Implement connection pooling for S3 access
  - Monitor and optimize data transfer costs

#### User Story 3.3: Data Transformation Pipeline
- **As an** AI agent
- **I want** basketball data in a consistent, well-structured format
- **So that** I can easily analyze and present statistics
- **Acceptance Criteria:**
  - Transform Parquet data into MCP-compliant response formats
  - Implement data validation and quality checks
  - Support multiple output formats (JSON, structured text)
  - Handle data aggregation and summarization
  - Provide metadata about data freshness and quality

### Epic 4: Basketball Analytics Endpoints
**Goal:** Implement specific MCP endpoints for basketball statistics access

#### User Story 4.1: Player Season Statistics Endpoint
- **As an** AI agent
- **I want** to retrieve season statistics for any NBA player
- **So that** I can provide detailed player analysis and comparisons
- **Acceptance Criteria:**
  - Implement `getPlayerSeasonStats(player_name, season)` endpoint
  - Support fuzzy player name matching and suggestions
  - Return comprehensive season statistics (scoring, rebounds, assists, etc.)
  - Include metadata about games played, team affiliations
  - Support multiple seasons and career aggregations

#### User Story 4.2: Team Performance Data Endpoint
- **As an** AI agent
- **I want** to access team-level statistics and performance data
- **So that** I can analyze team dynamics and historical performance
- **Acceptance Criteria:**
  - Implement team statistics retrieval by season and team name
  - Support roster information and player composition
  - Include team performance metrics and rankings
  - Provide head-to-head comparison capabilities
  - Support historical team data across multiple seasons

#### User Story 4.3: Game and Schedule Data Endpoint
- **As an** AI agent
- **I want** to access individual game data and scheduling information
- **So that** I can provide context about specific games and upcoming matches
- **Acceptance Criteria:**
  - Implement game-by-game statistics retrieval
  - Support date-based and team-based game queries
  - Include box scores, player performances, and game context
  - Provide schedule information for upcoming games
  - Support playoff and regular season differentiation

### Epic 5: Security and Authentication
**Goal:** Implement robust security measures for the MCP server

#### User Story 5.1: API Key Authentication System
- **As a** system administrator
- **I want** to control access to the MCP server through API keys
- **So that** usage can be monitored and access can be revoked if needed
- **Acceptance Criteria:**
  - Implement API key generation and management system
  - Integrate API key validation with API Gateway
  - Support multiple API key tiers (development, production, premium)
  - Log API key usage for monitoring and billing
  - Provide API key rotation capabilities

#### User Story 5.2: Rate Limiting and Throttling
- **As a** resource management system
- **I want** to prevent abuse and ensure fair usage of the MCP server
- **So that** the service remains available and cost-effective for all users
- **Acceptance Criteria:**
  - Implement per-API-key rate limiting policies
  - Configure burst and sustained rate limits
  - Provide clear error messages for rate limit violations
  - Support different rate limits for different endpoint types
  - Monitor and alert on unusual usage patterns

#### User Story 5.3: Request Validation and Sanitization
- **As a** security-focused system
- **I want** to validate and sanitize all incoming requests
- **So that** the system is protected from malicious or malformed input
- **Acceptance Criteria:**
  - Implement input validation for all MCP endpoint parameters
  - Sanitize user input to prevent injection attacks
  - Validate request structure against MCP protocol schemas
  - Implement proper error handling without information leakage
  - Log security-relevant events for monitoring

### Epic 6: Monitoring and Observability
**Goal:** Implement comprehensive monitoring and logging for operational visibility

#### User Story 6.1: Application Performance Monitoring
- **As an** operations engineer
- **I want** to monitor MCP server performance and health
- **So that** I can ensure reliable service and quickly identify issues
- **Acceptance Criteria:**
  - Implement CloudWatch metrics for Lambda performance
  - Monitor API Gateway request patterns and latencies
  - Track data access patterns and S3 costs
  - Set up automated alerting for performance degradation
  - Create operational dashboards for system health

#### User Story 6.2: Business Intelligence Metrics
- **As a** product manager
- **I want** to understand how the MCP server is being used
- **So that** I can make informed decisions about feature development
- **Acceptance Criteria:**
  - Track endpoint usage patterns and popular queries
  - Monitor user engagement and API adoption
  - Measure data freshness and quality metrics
  - Analyze cost efficiency and resource utilization
  - Generate usage reports for stakeholders

#### User Story 6.3: Error Tracking and Debugging
- **As a** developer
- **I want** comprehensive error tracking and debugging capabilities
- **So that** I can quickly identify and resolve issues
- **Acceptance Criteria:**
  - Implement structured logging throughout the application
  - Track and categorize error types and frequencies
  - Provide detailed error context for debugging
  - Set up automated error alerting and escalation
  - Create error analysis and trending reports

## Required ADRs

The following ADRs need to be proposed to formalize the architectural decisions for this MCP server implementation:

### ADR: Model Context Protocol Version and Implementation Strategy
- **Decision Needed:** Which MCP version to implement and how strictly to adhere to the specification
- **Context:** MCP is an evolving protocol with multiple versions and implementation approaches
- **Key Considerations:**
  - Protocol stability and future compatibility
  - Available Python libraries and tooling
  - AI agent compatibility requirements
  - Extension and customization capabilities

### ADR: API Gateway Configuration and Routing Strategy  
- **Decision Needed:** How to structure API Gateway endpoints, routing, and integration patterns
- **Context:** Need scalable, maintainable API structure that supports MCP protocol requirements
- **Key Considerations:**
  - RESTful vs. GraphQL vs. MCP-specific patterns
  - Versioning and backward compatibility strategy
  - Request/response transformation requirements
  - CORS and cross-domain access policies

### ADR: Lambda Application Architecture and Framework Selection
- **Decision Needed:** Internal structure of the Python Lambda application and framework choice
- **Context:** Need maintainable, testable Lambda function architecture that supports MCP protocol
- **Key Considerations:**
  - Framework choice (FastAPI, Flask, pure Lambda, or MCP-specific frameworks)
  - Dependency injection and configuration patterns
  - Request routing and handler organization
  - Testing and local development strategies

### ADR: Data Access Layer Design and Caching Strategy
- **Decision Needed:** How to efficiently access and cache Parquet data from S3
- **Context:** Need cost-effective, performant data access that scales with usage
- **Key Considerations:**
  - AWS Data Wrangler vs. alternative libraries (pyarrow, pandas)
  - Caching strategies (Lambda memory, Redis, CloudFront)
  - Data partitioning and query optimization approaches
  - Connection pooling and resource management

### ADR: Authentication and Authorization Approach
- **Decision Needed:** Complete authentication strategy including API keys, authorization, and access control
- **Context:** Need secure access control that's easy to manage and scales with user growth
- **Key Considerations:**
  - API Gateway native authentication vs. custom Lambda authorizers
  - API key management and rotation strategies
  - User tiers and access level differentiation
  - Integration with existing identity systems

### ADR: Error Handling and Response Format Standards
- **Decision Needed:** Standardized error handling, logging, and response formatting approach
- **Context:** Need consistent, debuggable error handling that provides good developer experience
- **Key Considerations:**
  - MCP protocol error format compliance
  - Structured logging format and content
  - Error classification and escalation policies
  - Client-friendly error messages and documentation

### ADR: Cost Management and Resource Optimization Strategy
- **Decision Needed:** Approach to managing AWS costs and optimizing resource usage
- **Context:** Need cost-effective operation that scales efficiently with usage growth
- **Key Considerations:**
  - Lambda memory and timeout configurations
  - S3 access pattern optimization and cost control
  - API Gateway pricing model selection
  - Monitoring and alerting for cost management

## High-Level Implementation Strategy

### Phase 1: Core Infrastructure Foundation (Weeks 1-3)
1. **Terraform Infrastructure Setup**
   - Create Terraform modules for API Gateway, Lambda, and IAM roles
   - Set up S3 bucket access permissions for Gold layer data
   - Configure CloudWatch logging and basic monitoring
   - Establish CI/CD pipeline integration for infrastructure deployment

2. **Basic Lambda Function Framework**
   - Create Python Lambda function template following project standards
   - Implement basic MCP protocol response structure
   - Set up local development environment with Lambda emulation
   - Configure dependency management with Poetry and Lambda layers

3. **API Gateway Integration**
   - Configure API Gateway endpoints with Lambda integration
   - Implement basic authentication using API keys
   - Set up CORS policies and request validation
   - Configure rate limiting and throttling policies

4. **Data Access Foundation**
   - Implement basic S3 Parquet file reading using AWS Data Wrangler
   - Create data access abstraction layer for future optimization
   - Set up connection pooling and resource management
   - Implement basic error handling and logging

### Phase 2: MCP Protocol Implementation (Weeks 4-6)
1. **MCP Server Core Components**
   - Implement MCP resource discovery and capability negotiation
   - Create request/response handling framework
   - Add protocol validation and error handling
   - Implement JSON schema validation for requests and responses

2. **Basketball Data Endpoints**
   - Implement `getPlayerSeasonStats` endpoint with comprehensive functionality
   - Add player name fuzzy matching and suggestion capabilities
   - Create data transformation pipeline from Parquet to MCP format
   - Implement query optimization for common access patterns

3. **Security Implementation**
   - Complete API key management system
   - Add request validation and sanitization
   - Implement security logging and monitoring
   - Set up automated security testing in CI/CD

4. **Testing Infrastructure**
   - Create comprehensive test suite for MCP protocol compliance
   - Implement integration tests with real data scenarios
   - Add performance testing and benchmarking
   - Set up automated testing in CI/CD pipeline

### Phase 3: Enhanced Features and Optimization (Weeks 7-8)
1. **Additional Data Endpoints**
   - Implement team statistics and performance endpoints
   - Add game data and scheduling information access
   - Create aggregation and comparison capabilities
   - Support advanced filtering and querying options

2. **Performance Optimization**
   - Implement intelligent caching strategies
   - Optimize data access patterns and query performance
   - Add response compression and optimization
   - Tune Lambda resource allocation based on usage patterns

3. **Advanced Monitoring and Analytics**
   - Set up comprehensive CloudWatch dashboards
   - Implement business intelligence metrics collection
   - Create automated alerting and incident response procedures
   - Add cost analysis and optimization recommendations

4. **Documentation and Developer Experience**
   - Create comprehensive API documentation with examples
   - Implement interactive API explorer
   - Add client SDK examples and integration guides
   - Create troubleshooting and FAQ documentation

### Technical Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Agents     │    │   API Gateway    │    │  Lambda MCP     │
│                 │───▶│                  │───▶│    Server       │
│ - ChatGPT       │    │ - Authentication │    │                 │
│ - Claude        │    │ - Rate Limiting  │    │ - MCP Protocol  │
│ - Custom Bots   │    │ - Request Valid. │    │ - Data Access   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   AWS Services   │    │   Gold Layer    │
│                 │    │                  │    │                 │
│ - CloudWatch    │◀───│ - IAM Roles      │    │ - S3 Parquet    │
│ - Alarms        │    │ - Secrets Mgr    │    │ - Player Stats  │
│ - Dashboards    │    │ - Parameter Store│    │ - Team Data     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Implementation Principles

1. **MCP Protocol Compliance:** Strict adherence to Model Context Protocol specifications for maximum compatibility
2. **Serverless-First Architecture:** Leverage AWS Lambda and managed services for cost efficiency and scalability
3. **Data Access Optimization:** Efficient Parquet querying with intelligent caching to minimize costs
4. **Security by Design:** Comprehensive authentication, authorization, and input validation
5. **Observability First:** Extensive logging, monitoring, and alerting from day one
6. **Developer Experience:** Clear documentation, examples, and tooling for easy integration

## Risks & Open Questions

### High Priority Risks

#### Risk: MCP Protocol Evolution and Compatibility
- **Description:** The Model Context Protocol is still evolving, and future changes could break our implementation
- **Impact:** Could require significant refactoring or limit AI agent compatibility
- **Mitigation:** Implement versioning strategy, monitor MCP specification updates, design flexible protocol abstraction layer

#### Risk: AWS Lambda Cold Start Performance
- **Description:** Lambda cold starts could cause unacceptable latency for time-sensitive AI agent interactions
- **Impact:** Poor user experience and potential timeout issues for AI agents
- **Mitigation:** Implement Lambda warming strategies, optimize package size, consider provisioned concurrency for critical endpoints

#### Risk: Data Access Cost Escalation
- **Description:** High-frequency AI agent queries could result in unexpected S3 and data transfer costs
- **Impact:** Could make the service financially unsustainable
- **Mitigation:** Implement intelligent caching, optimize query patterns, set up cost monitoring and alerting, design usage-based pricing tiers

#### Risk: API Key Management and Security
- **Description:** API key compromise or inadequate access controls could lead to service abuse or data breaches
- **Impact:** Potential service disruption, data exposure, or financial impact from abuse
- **Mitigation:** Implement proper key rotation, usage monitoring, rate limiting, and automated abuse detection

### Medium Priority Risks

#### Risk: Parquet File Schema Evolution
- **Description:** Changes to the Gold layer data schema could break the MCP server data access
- **Impact:** Could cause service failures or data inconsistency issues
- **Mitigation:** Implement schema validation, version detection, and backward compatibility handling

#### Risk: AI Agent Authentication Complexity
- **Description:** Different AI platforms may have varying authentication requirements or limitations
- **Impact:** Could limit adoption or require complex authentication flows
- **Mitigation:** Research common AI agent authentication patterns, design flexible authentication system

#### Risk: Regulatory and Compliance Requirements
- **Description:** Data privacy regulations might impose restrictions on data access or logging
- **Impact:** Could require significant architectural changes or limit functionality
- **Mitigation:** Research applicable regulations, implement privacy-by-design principles, prepare for compliance requirements

### Open Questions

#### Question: MCP Protocol Extension Requirements
- **Question:** Should we implement custom MCP extensions for basketball-specific functionality?
- **Impact:** Affects protocol compliance vs. feature richness trade-offs
- **Investigation Needed:** Analyze AI agent capabilities, study MCP extension patterns, evaluate custom functionality benefits

#### Question: Multi-Sport Data Expansion Strategy
- **Question:** How should the architecture accommodate future expansion to other sports (WNBA, international leagues)?
- **Impact:** Affects data modeling, endpoint design, and resource organization
- **Investigation Needed:** Evaluate data commonalities across sports, assess scaling requirements

#### Question: Real-Time Data Integration
- **Question:** Should the MCP server support real-time or near-real-time data for live games?
- **Impact:** Affects architecture complexity, caching strategies, and cost model
- **Investigation Needed:** Assess real-time data requirements, evaluate streaming vs. batch processing trade-offs

#### Question: AI Agent Usage Patterns and Scaling
- **Question:** What are the expected usage patterns and scaling requirements for AI agent interactions?
- **Impact:** Affects resource allocation, caching strategies, and cost optimization
- **Investigation Needed:** Research AI agent usage patterns, model expected growth, design capacity planning

#### Question: Data Aggregation and Preprocessing
- **Question:** Should complex aggregations be pre-computed or calculated on-demand?
- **Impact:** Affects storage costs, response times, and data freshness
- **Investigation Needed:** Analyze common query patterns, evaluate storage vs. compute cost trade-offs

### Future Considerations

#### Consideration: Multi-Modal Data Support
- **Question:** Should the MCP server support non-tabular data like images, videos, or audio?
- **Investigation:** Evaluate MCP protocol support for binary data, assess basketball media data value

#### Consideration: AI Agent Feedback Loop
- **Question:** Should the system learn from AI agent usage patterns to optimize responses?
- **Investigation:** Explore machine learning integration possibilities, evaluate privacy implications

#### Consideration: Collaborative AI Features
- **Question:** Should the system support multiple AI agents working together on complex analyses?
- **Investigation:** Research multi-agent coordination patterns, assess architectural requirements

---

## Success Criteria

This MCP server implementation is considered successful when it meets these measurable criteria:

### Functional Success Criteria
1. **Protocol Compliance:** Successfully passes automated MCP protocol compliance tests
2. **Core Functionality:** AI agents can reliably retrieve player season statistics with <2 second response times
3. **Data Accuracy:** 100% accuracy between MCP responses and source Gold layer data
4. **Availability:** 99.9% uptime during normal operations with proper error handling

### Technical Success Criteria
1. **Performance:** Average response time <500ms for cached queries, <2s for complex aggregations
2. **Scalability:** Can handle 1000+ concurrent requests without degradation
3. **Cost Efficiency:** Monthly AWS costs remain under $100 for moderate usage patterns
4. **Security:** Zero security incidents, all authentication working correctly

### Business Success Criteria
1. **AI Agent Adoption:** At least 3 different AI platforms successfully integrate and use the service
2. **Data Value Demonstration:** Can provide meaningful basketball insights through AI interactions
3. **Developer Experience:** Comprehensive documentation enables independent integration by external developers
4. **Foundation for Growth:** Architecture supports adding new data types and endpoints without major refactoring

### Operational Success Criteria
1. **Monitoring Coverage:** All critical paths have appropriate monitoring and alerting
2. **Incident Response:** Mean time to resolution for issues <1 hour during business hours
3. **Documentation Quality:** All APIs documented with examples, troubleshooting guides available
4. **Maintainability:** New team members can understand and extend the system within 1 week

---

**Implementation Timeline Estimate:**
- Phase 1 (Infrastructure): 3 weeks
- Phase 2 (MCP Implementation): 3 weeks  
- Phase 3 (Optimization): 2 weeks
- **Total:** 8 weeks for complete implementation

**Dependencies:**
- Gold layer data availability and access permissions
- AWS account setup and authentication configuration
- MCP protocol specification stability and documentation
- Testing infrastructure for protocol compliance validation

*This plan builds upon existing architectural decisions in ADR-009 (AWS cloud), ADR-010 (Terraform), ADR-013 (NBA API data), and ADR-014 (Parquet storage), ensuring consistency with established project direction.*