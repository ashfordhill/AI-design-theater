"""Mermaid diagram generation from design documents."""

import re
from typing import List, Dict, Any, Optional
from ..models import DesignDocument
from ..config import config


class MermaidGenerator:
    """Generates Mermaid diagrams from design conversations."""
    
    def generate_architecture_diagram(self, design_doc: DesignDocument, detail_level: int = 5) -> str:
        """Generate a Mermaid architecture diagram from the design document.

        Uses a neutral LLM to create professional diagrams independent of conversation content.
        detail_level (1-10) influences richness; >6 attempts component style.
        """
        # Use neutral LLM to generate professional architecture independent of conversation
        if (detail_level >= 5 or 
            any(word in design_doc.title.lower() for word in ['api', 'gateway', 'system', 'service', 'architecture', 'platform', 'application'])):
            return self._generate_llm_architecture_diagram(design_doc, detail_level)
        
        # Fallback to old approach for simpler topics
        content = self._get_all_content(design_doc)
        if self._is_sequence_suitable(content):
            return self._generate_sequence_diagram(design_doc)
        if self._is_class_suitable(content):
            return self._generate_class_diagram(design_doc)
        if self._is_flowchart_suitable(content):
            return self._generate_flowchart(design_doc)
        
        return self._generate_generic_graph(design_doc)

    def _generate_llm_architecture_diagram(self, design_doc: DesignDocument, detail_level: int) -> str:
        """Use a neutral LLM to generate professional software architecture diagrams."""
        try:
            # Use OpenAI for consistent, professional architecture generation
            if not config.openai_api_key:
                print("OpenAI API key not available, falling back to smart defaults")
                return self._generate_component_graph_fallback(design_doc, detail_level)
                
            # Use direct OpenAI API call for synchronous diagram generation
            import openai
            
            system_prompt = """You are a professional software architect. Generate a realistic, professional software architecture for the given topic.

Create a JSON response with this exact structure:
{
  "components": {
    "componentId": {
      "label": "Component Name\\n(Technology)",
      "type": "user|api|service|database|cache|external"
    }
  },
  "connections": [
    {"from": "sourceId", "to": "targetId", "label": "connection type"}
  ]
}

Focus on:
- Realistic components (Load Balancer, API Gateway, specific services, databases)
- Proper technology choices (PostgreSQL, Redis, Kafka, etc.)
- Logical data flows and connections
- Production-ready architecture patterns

Do not include conversation content or entertainment elements. Generate serious, professional architecture only."""

            user_prompt = f"Generate a professional software architecture for: {design_doc.title}\n\nCreate realistic components, technologies, and connections for this system."
            
            # Direct OpenAI API call
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            
            # Parse LLM response and generate diagram
            return self._create_mermaid_from_llm_response(response_text, design_doc.title)
            
        except Exception as e:
            print(f"LLM diagram generation failed: {e}, falling back to smart defaults")
            return self._generate_component_graph_fallback(design_doc, detail_level)
    
    def _create_mermaid_from_llm_response(self, llm_response: str, title: str) -> str:
        """Convert LLM JSON response into professional Mermaid diagram."""
        import json
        
        try:
            # Extract JSON from response (handle potential markdown wrapping)
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                arch_data = json.loads(llm_response[json_start:json_end])
            else:
                raise ValueError("No valid JSON found in response")
            
            mermaid = ["graph TB", ""]
            
            # Add professional styling
            mermaid.extend([
                "    %% Professional Software Architecture Styling",
                "    classDef userInterface fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000",
                "    classDef apiLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000", 
                "    classDef service fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000",
                "    classDef database fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000",
                "    classDef cache fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000",
                "    classDef external fill:#f1f8e9,stroke:#33691e,stroke-width:2px,color:#000",
                ""
            ])
            
            # Add components with proper shapes
            for comp_id, comp_info in arch_data["components"].items():
                comp_type = comp_info["type"]
                label = comp_info["label"]
                
                if comp_type == "user":
                    mermaid.append(f"    {comp_id}(({label}))")
                elif comp_type == "database":
                    mermaid.append(f"    {comp_id}[({label})]")
                elif comp_type == "cache":
                    mermaid.append(f"    {comp_id}{{{{({label})}}}}") 
                elif comp_type == "external":
                    mermaid.append(f"    {comp_id}[[{label}]]")
                else:  # api, service
                    mermaid.append(f"    {comp_id}[{label}]")
            
            mermaid.append("")
            
            # Add connections
            for conn in arch_data["connections"]:
                from_comp = conn["from"]
                to_comp = conn["to"]
                label = conn.get("label", "")
                
                if label:
                    mermaid.append(f"    {from_comp} -->|{label}| {to_comp}")
                else:
                    mermaid.append(f"    {from_comp} --> {to_comp}")
            
            mermaid.append("")
            
            # Apply styling classes
            for comp_id, comp_info in arch_data["components"].items():
                comp_type = comp_info["type"]
                if comp_type == "user":
                    style_class = "userInterface"
                elif comp_type == "api":
                    style_class = "apiLayer"
                elif comp_type == "service":
                    style_class = "service"
                elif comp_type == "database":
                    style_class = "database"
                elif comp_type == "cache":
                    style_class = "cache"
                elif comp_type == "external":
                    style_class = "external"
                else:
                    style_class = "service"  # default
                
                mermaid.append(f"    class {comp_id} {style_class}")
            
            return "\n".join(mermaid)
            
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            # Return a simple professional fallback
            return self._generate_smart_fallback(title)
    
    def _generate_smart_fallback(self, title: str) -> str:
        """Generate a smart fallback diagram based on title keywords."""
        components = self._get_smart_defaults_for_topic(title)
        
        mermaid = ["graph TB", ""]
        mermaid.extend([
            "    %% Professional Fallback Architecture",
            "    classDef userInterface fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000",
            "    classDef apiLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000", 
            "    classDef service fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000",
            "    classDef database fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000",
            "    classDef cache fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000",
            "    classDef external fill:#f1f8e9,stroke:#33691e,stroke-width:2px,color:#000",
            ""
        ])
        
        # Add components with proper shapes
        for comp_id, comp_info in components.items():
            comp_type = comp_info["type"]
            label = comp_info["label"]
            
            if comp_type == "user":
                mermaid.append(f"    {comp_id}(({label}))")
            elif comp_type == "database":
                mermaid.append(f"    {comp_id}[({label})]")
            elif comp_type == "cache":
                mermaid.append(f"    {comp_id}{{{{({label})}}}}") 
            elif comp_type == "external":
                mermaid.append(f"    {comp_id}[[{label}]]")
            else:  # api, service
                mermaid.append(f"    {comp_id}[{label}]")
        
        mermaid.append("")
        
        # Add smart connections based on title
        edges = self._generate_smart_edges(components, type('MockDoc', (), {'title': title})())
        mermaid.extend([f"    {edge}" for edge in edges])
        
        mermaid.append("")
        
        # Apply styling classes
        for comp_id, comp_info in components.items():
            comp_type = comp_info["type"]
            style_class = {
                "user": "userInterface",
                "api": "apiLayer", 
                "service": "service",
                "database": "database",
                "cache": "cache",
                "external": "external"
            }.get(comp_type, "service")
            
            mermaid.append(f"    class {comp_id} {style_class}")
        
        return "\n".join(mermaid)
    
    def _generate_component_graph_fallback(self, design_doc: DesignDocument, detail_level: int) -> str:
        """Generate a richer software architecture component diagram (graph TB) - FALLBACK."""
        mermaid = ["graph TB"]  # Top-bottom for better readability
        
        # Use smart defaults for the topic
        actual_components = self._get_smart_defaults_for_topic(design_doc.title)
        
        # Add styling classes
        mermaid.append("")
        mermaid.append("    %% Styling")
        mermaid.append("    classDef userInterface fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000")
        mermaid.append("    classDef apiLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000")
        mermaid.append("    classDef service fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000")
        mermaid.append("    classDef database fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000")
        mermaid.append("    classDef cache fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000")
        mermaid.append("    classDef external fill:#f1f8e9,stroke:#33691e,stroke-width:2px,color:#000")
        mermaid.append("")
        
        # Generate nodes with proper styling
        node_classes = {}
        for comp_id, comp_info in actual_components.items():
            label = comp_info['label']
            comp_type = comp_info['type']
            
            # Choose node shape based on type
            if comp_type == 'user':
                mermaid.append(f"    {comp_id}(({label}))")
                node_classes[comp_id] = "userInterface"
            elif comp_type == 'api':
                mermaid.append(f"    {comp_id}[{label}]")
                node_classes[comp_id] = "apiLayer"
            elif comp_type == 'service':
                mermaid.append(f"    {comp_id}[{label}]")
                node_classes[comp_id] = "service"
            elif comp_type == 'database':
                mermaid.append(f"    {comp_id}[(({label})])")
                node_classes[comp_id] = "database"
            elif comp_type == 'cache':
                mermaid.append(f"    {comp_id}[{label}]")
                node_classes[comp_id] = "cache"
            elif comp_type == 'external':
                mermaid.append(f"    {comp_id}{{{label}}}")
                node_classes[comp_id] = "external"
            else:
                mermaid.append(f"    {comp_id}[{label}]")
                node_classes[comp_id] = "service"
        
        mermaid.append("")
        
        # Generate smart connections based on component types and content
        edges = self._generate_smart_edges(actual_components, design_doc)
        
        for edge in edges:
            mermaid.append(f"    {edge}")
        
        mermaid.append("")
        
        # Apply styling classes
        for comp_id, class_name in node_classes.items():
            mermaid.append(f"    class {comp_id} {class_name}")
        
        return "\n".join(mermaid)
    
    def _extract_architecture_components(self, design_doc: DesignDocument) -> Dict[str, Dict[str, str]]:
        """Extract actual architectural components from the design conversation."""
        components = {}
        all_text = (design_doc.description + " " + 
                   " ".join(design_doc.key_decisions) + " " + 
                   " ".join(design_doc.implementation_notes)).lower()
        
        # Component patterns with types
        patterns = {
            # APIs and Gateways
            r'\b(graphql.*gateway|api.*gateway|gateway)\b': ('apiGW', 'GraphQL Gateway', 'api'),
            r'\b(apollo.*server|graphql.*server)\b': ('apollo', 'Apollo Server', 'api'),
            r'\b(rest.*api|microservice)\b': ('restAPI', 'REST APIs', 'external'),
            
            # Authentication
            r'\b(auth.*service|authentication|jwt|oauth)\b': ('auth', 'Authentication', 'service'),
            
            # Databases
            r'\b(database|postgres|mysql|mongo|redis.*db)\b': ('db', 'Database', 'database'),
            r'\b(cache|redis.*cache)\b': ('cache', 'Cache Layer', 'cache'),
            
            # Services
            r'\b(user.*service|user.*management)\b': ('userSvc', 'User Service', 'service'),
            r'\b(notification.*service)\b': ('notifSvc', 'Notification Service', 'service'),
            r'\b(fraud.*detection|fraud.*system)\b': ('fraudSvc', 'Fraud Detection', 'service'),
            r'\b(payment.*service|billing)\b': ('paymentSvc', 'Payment Service', 'service'),
            
            # Infrastructure
            r'\b(load.*balancer|lb)\b': ('lb', 'Load Balancer', 'api'),
            r'\b(cdn|content.*delivery)\b': ('cdn', 'CDN', 'external'),
            r'\b(queue|message.*queue|kafka|rabbitmq)\b': ('queue', 'Message Queue', 'service'),
            
            # Client/UI
            r'\b(client|frontend|ui|user.*interface)\b': ('client', 'Client App', 'user'),
            r'\b(mobile.*app|web.*app)\b': ('app', 'Mobile/Web App', 'user'),
        }
        
        for pattern, (comp_id, label, comp_type) in patterns.items():
            if re.search(pattern, all_text):
                components[comp_id] = {'label': label, 'type': comp_type}
        
        return components
    
    def _get_smart_defaults_for_topic(self, title: str) -> Dict[str, Dict[str, str]]:
        """Get realistic software architecture components based on the project title."""
        title_lower = title.lower()
        
        if 'graphql' in title_lower or 'api.*gateway' in title_lower:
            return {
                'clients': {'label': 'Client Apps\n(Web/Mobile)', 'type': 'user'},
                'lb': {'label': 'Load Balancer\n(NGINX)', 'type': 'api'},
                'gateway': {'label': 'GraphQL Gateway\n(Apollo)', 'type': 'api'},
                'authSvc': {'label': 'Auth Service\n(JWT)', 'type': 'service'},
                'userSvc': {'label': 'User Service', 'type': 'service'},
                'productSvc': {'label': 'Product Service', 'type': 'service'},
                'redis': {'label': 'Redis\n(Cache)', 'type': 'cache'},
                'userDB': {'label': 'User DB\n(PostgreSQL)', 'type': 'database'},
                'productDB': {'label': 'Product DB\n(MongoDB)', 'type': 'database'},
                'monitoring': {'label': 'Monitoring\n(Prometheus)', 'type': 'external'}
            }
        elif 'caching' in title_lower or 'cache' in title_lower:
            return {
                'apps': {'label': 'Applications', 'type': 'user'},
                'lb': {'label': 'Load Balancer', 'type': 'api'},
                'appServers': {'label': 'App Servers\n(Node.js)', 'type': 'service'},
                'l1Cache': {'label': 'L1 Cache\n(Redis)', 'type': 'cache'},
                'l2Cache': {'label': 'L2 Cache\n(Memcached)', 'type': 'cache'},
                'primaryDB': {'label': 'Primary DB\n(PostgreSQL)', 'type': 'database'},
                'readReplicas': {'label': 'Read Replicas', 'type': 'database'},
                'cdn': {'label': 'CDN\n(CloudFlare)', 'type': 'external'}
            }
        elif 'fraud' in title_lower:
            return {
                'transactions': {'label': 'Transaction\nRequests', 'type': 'user'},
                'gateway': {'label': 'API Gateway', 'type': 'api'},
                'ingestSvc': {'label': 'Data Ingestion\n(Kafka)', 'type': 'service'},
                'fraudEngine': {'label': 'Fraud Detection\nEngine', 'type': 'service'},
                'mlSvc': {'label': 'ML Scoring\nService', 'type': 'service'},
                'ruleEngine': {'label': 'Rules Engine', 'type': 'service'},
                'alertSvc': {'label': 'Alert Service', 'type': 'service'},
                'transactionDB': {'label': 'Transaction DB\n(Cassandra)', 'type': 'database'},
                'modelStore': {'label': 'Model Store\n(S3)', 'type': 'database'},
                'eventStream': {'label': 'Event Stream\n(Kafka)', 'type': 'external'}
            }
        elif 'saas' in title_lower or 'tenant' in title_lower:
            return {
                'tenants': {'label': 'Tenant Users', 'type': 'user'},
                'lb': {'label': 'Load Balancer', 'type': 'api'},
                'gateway': {'label': 'Multi-tenant\nAPI Gateway', 'type': 'api'},
                'authSvc': {'label': 'Auth & IAM\nService', 'type': 'service'},
                'tenantSvc': {'label': 'Tenant\nManagement', 'type': 'service'},
                'businessSvc': {'label': 'Business Logic\nServices', 'type': 'service'},
                'sharedDB': {'label': 'Shared DB\n(PostgreSQL)', 'type': 'database'},
                'tenantDBs': {'label': 'Tenant DBs\n(Sharded)', 'type': 'database'},
                'blobStore': {'label': 'Blob Storage\n(S3)', 'type': 'external'}
            }
        elif 'chat' in title_lower or 'real.*time' in title_lower:
            return {
                'clients': {'label': 'Chat Clients', 'type': 'user'},
                'wsGateway': {'label': 'WebSocket\nGateway', 'type': 'api'},
                'chatSvc': {'label': 'Chat Service', 'type': 'service'},
                'presenceSvc': {'label': 'Presence\nService', 'type': 'service'},
                'notificationSvc': {'label': 'Notification\nService', 'type': 'service'},
                'encryptionSvc': {'label': 'E2E Encryption\nService', 'type': 'service'},
                'messageDB': {'label': 'Message Store\n(MongoDB)', 'type': 'database'},
                'userDB': {'label': 'User DB\n(PostgreSQL)', 'type': 'database'},
                'messageQueue': {'label': 'Message Queue\n(RabbitMQ)', 'type': 'external'}
            }
        else:
            # Generic microservices system
            return {
                'users': {'label': 'Users', 'type': 'user'},
                'lb': {'label': 'Load Balancer', 'type': 'api'},
                'gateway': {'label': 'API Gateway', 'type': 'api'},
                'serviceA': {'label': 'Service A', 'type': 'service'},
                'serviceB': {'label': 'Service B', 'type': 'service'},
                'serviceC': {'label': 'Service C', 'type': 'service'},
                'cache': {'label': 'Cache\n(Redis)', 'type': 'cache'},
                'primaryDB': {'label': 'Database\n(PostgreSQL)', 'type': 'database'},
                'queue': {'label': 'Message Queue\n(Kafka)', 'type': 'external'}
            }
    
    def _generate_smart_edges(self, components: Dict[str, Dict[str, str]], design_doc: DesignDocument) -> List[str]:
        """Generate realistic software architecture connections."""
        edges = []
        comp_ids = list(components.keys())
        
        # Group components by type
        user_components = [cid for cid, info in components.items() if info['type'] == 'user']
        api_components = [cid for cid, info in components.items() if info['type'] == 'api']
        service_components = [cid for cid, info in components.items() if info['type'] == 'service']
        database_components = [cid for cid, info in components.items() if info['type'] == 'database']
        cache_components = [cid for cid, info in components.items() if info['type'] == 'cache']
        external_components = [cid for cid, info in components.items() if info['type'] == 'external']
        
        # Create realistic architecture flows
        title_lower = design_doc.title.lower()
        
        if 'graphql' in title_lower or 'gateway' in title_lower:
            self._add_graphql_flows(edges, components)
        elif 'fraud' in title_lower:
            self._add_fraud_detection_flows(edges, components)
        elif 'cache' in title_lower:
            self._add_caching_flows(edges, components)
        elif 'saas' in title_lower or 'tenant' in title_lower:
            self._add_saas_flows(edges, components)
        elif 'chat' in title_lower:
            self._add_chat_flows(edges, components)
        else:
            self._add_generic_microservice_flows(edges, components)
        
        return edges
    
    def _add_graphql_flows(self, edges: List[str], components: Dict[str, Dict[str, str]]):
        """Add GraphQL-specific architecture flows."""
        if 'clients' in components and 'lb' in components:
            edges.append("clients -->|HTTPS| lb")
        if 'lb' in components and 'gateway' in components:
            edges.append("lb --> gateway")
        if 'gateway' in components and 'authSvc' in components:
            edges.append("gateway -->|validate| authSvc")
        if 'gateway' in components and 'userSvc' in components:
            edges.append("gateway -->|resolve| userSvc")
        if 'gateway' in components and 'productSvc' in components:
            edges.append("gateway -->|resolve| productSvc")
        if 'userSvc' in components and 'redis' in components:
            edges.append("userSvc <-->|cache| redis")
        if 'userSvc' in components and 'userDB' in components:
            edges.append("userSvc -->|SQL| userDB")
        if 'productSvc' in components and 'productDB' in components:
            edges.append("productSvc -->|NoSQL| productDB")
        if 'gateway' in components and 'monitoring' in components:
            edges.append("gateway -->|metrics| monitoring")
    
    def _add_fraud_detection_flows(self, edges: List[str], components: Dict[str, Dict[str, str]]):
        """Add fraud detection system flows."""
        if 'transactions' in components and 'gateway' in components:
            edges.append("transactions -->|POST| gateway")
        if 'gateway' in components and 'ingestSvc' in components:
            edges.append("gateway --> ingestSvc")
        if 'ingestSvc' in components and 'fraudEngine' in components:
            edges.append("ingestSvc -->|stream| fraudEngine")
        if 'fraudEngine' in components and 'mlSvc' in components:
            edges.append("fraudEngine -->|score| mlSvc")
        if 'fraudEngine' in components and 'ruleEngine' in components:
            edges.append("fraudEngine -->|validate| ruleEngine")
        if 'fraudEngine' in components and 'alertSvc' in components:
            edges.append("fraudEngine -->|alert| alertSvc")
        if 'ingestSvc' in components and 'transactionDB' in components:
            edges.append("ingestSvc -->|store| transactionDB")
        if 'mlSvc' in components and 'modelStore' in components:
            edges.append("mlSvc <-->|models| modelStore")
        if 'ingestSvc' in components and 'eventStream' in components:
            edges.append("ingestSvc -->|publish| eventStream")
    
    def _add_caching_flows(self, edges: List[str], components: Dict[str, Dict[str, str]]):
        """Add caching system flows."""
        if 'apps' in components and 'lb' in components:
            edges.append("apps --> lb")
        if 'lb' in components and 'appServers' in components:
            edges.append("lb --> appServers")
        if 'appServers' in components and 'l1Cache' in components:
            edges.append("appServers <-->|hot| l1Cache")
        if 'appServers' in components and 'l2Cache' in components:
            edges.append("appServers <-->|warm| l2Cache")
        if 'appServers' in components and 'primaryDB' in components:
            edges.append("appServers -->|write| primaryDB")
        if 'appServers' in components and 'readReplicas' in components:
            edges.append("appServers -->|read| readReplicas")
        if 'primaryDB' in components and 'readReplicas' in components:
            edges.append("primaryDB -->|replicate| readReplicas")
        if 'apps' in components and 'cdn' in components:
            edges.append("apps <-->|static| cdn")
    
    def _add_saas_flows(self, edges: List[str], components: Dict[str, Dict[str, str]]):
        """Add SaaS multi-tenant flows."""
        if 'tenants' in components and 'lb' in components:
            edges.append("tenants --> lb")
        if 'lb' in components and 'gateway' in components:
            edges.append("lb --> gateway")
        if 'gateway' in components and 'authSvc' in components:
            edges.append("gateway -->|auth| authSvc")
        if 'gateway' in components and 'tenantSvc' in components:
            edges.append("gateway -->|route| tenantSvc")
        if 'tenantSvc' in components and 'businessSvc' in components:
            edges.append("tenantSvc --> businessSvc")
        if 'authSvc' in components and 'sharedDB' in components:
            edges.append("authSvc -->|users| sharedDB")
        if 'businessSvc' in components and 'tenantDBs' in components:
            edges.append("businessSvc -->|tenant data| tenantDBs")
        if 'businessSvc' in components and 'blobStore' in components:
            edges.append("businessSvc <-->|files| blobStore")
    
    def _add_chat_flows(self, edges: List[str], components: Dict[str, Dict[str, str]]):
        """Add real-time chat flows."""
        if 'clients' in components and 'wsGateway' in components:
            edges.append("clients <-->|WebSocket| wsGateway")
        if 'wsGateway' in components and 'chatSvc' in components:
            edges.append("wsGateway <--> chatSvc")
        if 'wsGateway' in components and 'presenceSvc' in components:
            edges.append("wsGateway --> presenceSvc")
        if 'chatSvc' in components and 'encryptionSvc' in components:
            edges.append("chatSvc -->|encrypt| encryptionSvc")
        if 'chatSvc' in components and 'notificationSvc' in components:
            edges.append("chatSvc --> notificationSvc")
        if 'chatSvc' in components and 'messageDB' in components:
            edges.append("chatSvc -->|store| messageDB")
        if 'presenceSvc' in components and 'userDB' in components:
            edges.append("presenceSvc --> userDB")
        if 'chatSvc' in components and 'messageQueue' in components:
            edges.append("chatSvc -->|async| messageQueue")
    
    def _add_generic_microservice_flows(self, edges: List[str], components: Dict[str, Dict[str, str]]):
        """Add generic microservice flows."""
        if 'users' in components and 'lb' in components:
            edges.append("users --> lb")
        if 'lb' in components and 'gateway' in components:
            edges.append("lb --> gateway")
        if 'gateway' in components and 'serviceA' in components:
            edges.append("gateway --> serviceA")
        if 'gateway' in components and 'serviceB' in components:
            edges.append("gateway --> serviceB")
        if 'serviceA' in components and 'serviceC' in components:
            edges.append("serviceA --> serviceC")
        if 'serviceA' in components and 'cache' in components:
            edges.append("serviceA <--> cache")
        if 'serviceB' in components and 'primaryDB' in components:
            edges.append("serviceB --> primaryDB")
        if 'serviceC' in components and 'primaryDB' in components:
            edges.append("serviceC --> primaryDB")
        if 'serviceA' in components and 'queue' in components:
            edges.append("serviceA -->|async| queue")
    
    def _get_all_content(self, design_doc: DesignDocument) -> str:
        """Get all textual content from the design document."""
        content = f"{design_doc.title} {design_doc.description} "
        content += " ".join(design_doc.key_decisions)
        content += " ".join(design_doc.implementation_notes)
        return content.lower()
    
    def _is_flowchart_suitable(self, content: str) -> bool:
        """Check if content suggests a flowchart diagram."""
        flowchart_indicators = [
            "process", "workflow", "step", "flow", "pipeline", "sequence",
            "first", "then", "next", "finally", "after", "before"
        ]
        return any(indicator in content for indicator in flowchart_indicators)
    
    def _is_sequence_suitable(self, content: str) -> bool:
        """Check if content suggests a sequence diagram."""
        sequence_indicators = [
            "user", "client", "server", "api", "request", "response",
            "interaction", "communication", "message", "call"
        ]
        return any(indicator in content for indicator in sequence_indicators)
    
    def _is_class_suitable(self, content: str) -> bool:
        """Check if content suggests a class diagram."""
        class_indicators = [
            "class", "object", "inheritance", "interface", "model",
            "entity", "relationship", "attribute", "method"
        ]
        return any(indicator in content for indicator in class_indicators)
    
    def _generate_flowchart(self, design_doc: DesignDocument) -> str:
        """Generate a flowchart diagram."""
        mermaid = ["flowchart TD"]
        
        # Extract steps from implementation notes and decisions
        steps = self._extract_steps(design_doc)
        
        if not steps:
            steps = self._get_smart_process_steps(design_doc.title)
        
        # Add styling
        mermaid.append("")
        mermaid.append("    %% Styling")
        mermaid.append("    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000")
        mermaid.append("    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000")
        mermaid.append("    classDef decision fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000")
        mermaid.append("    classDef critical fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000")
        mermaid.append("")
        
        # Generate nodes with better styling
        node_classes = {}
        for i, step in enumerate(steps):
            node_id = f"A{i+1}"
            clean_step = self._clean_text_for_mermaid(step)
            
            if i == 0:  # Start node
                mermaid.append(f"    {node_id}([{clean_step}])")
                node_classes[node_id] = "startEnd"
            elif i == len(steps) - 1:  # End node
                mermaid.append(f"    {node_id}([{clean_step}])")
                node_classes[node_id] = "startEnd"
            elif any(word in step.lower() for word in ["decision", "choose", "validate", "check", "verify"]):
                mermaid.append(f"    {node_id}{{{clean_step}}}")
                node_classes[node_id] = "decision"
            elif any(word in step.lower() for word in ["error", "fail", "rollback", "alert"]):
                mermaid.append(f"    {node_id}[{clean_step}]")
                node_classes[node_id] = "critical"
            else:
                mermaid.append(f"    {node_id}[{clean_step}]")
                node_classes[node_id] = "process"
        
        mermaid.append("")
        
        # Generate connections with labels
        for i in range(len(steps) - 1):
            step = steps[i].lower()
            if "decision" in step or "check" in step or "validate" in step:
                mermaid.append(f"    A{i+1} -->|yes| A{i+2}")
                # Add alternate path if it's a decision
                if i+2 < len(steps):
                    mermaid.append(f"    A{i+1} -->|no| A{min(i+3, len(steps))}")
            else:
                mermaid.append(f"    A{i+1} --> A{i+2}")
        
        mermaid.append("")
        
        # Apply styling classes
        for node_id, class_name in node_classes.items():
            mermaid.append(f"    class {node_id} {class_name}")
        
        return "\n".join(mermaid)
    
    def _get_smart_process_steps(self, title: str) -> List[str]:
        """Get smart default process steps based on the project title."""
        title_lower = title.lower()
        
        if 'api' in title_lower or 'gateway' in title_lower:
            return [
                "Client Request",
                "Authentication Check", 
                "Route to Service",
                "Process Request",
                "Validate Response",
                "Return to Client"
            ]
        elif 'fraud' in title_lower:
            return [
                "Transaction Initiated",
                "Real-time Analysis",
                "Risk Score Calculation",
                "Decision: Block or Allow",
                "Log & Alert if Fraud",
                "Complete Transaction"
            ]
        elif 'cache' in title_lower:
            return [
                "Request Received",
                "Check Cache Hit",
                "Fetch from Database",
                "Update Cache",
                "Return Data"
            ]
        elif 'saas' in title_lower:
            return [
                "User Login",
                "Tenant Identification",
                "Authorization Check",
                "Route to Tenant Data",
                "Process Request",
                "Return Response"
            ]
        elif 'chat' in title_lower:
            return [
                "Message Sent",
                "Encrypt Message",
                "Validate Recipients",
                "Deliver to Active Users",
                "Store in History",
                "Confirm Delivery"
            ]
        else:
            return [
                "Initialize System",
                "Validate Input",
                "Process Data", 
                "Execute Business Logic",
                "Store Results",
                "Complete Operation"
            ]
    
    def _generate_sequence_diagram(self, design_doc: DesignDocument) -> str:
        """Generate a sequence diagram."""
        mermaid = "sequenceDiagram\n"
        
        # Extract actors and interactions
        actors = self._extract_actors(design_doc)
        interactions = self._extract_interactions(design_doc)
        
        if not actors:
            actors = ["User", "System", "Database"]
        
        # Add participants
        for actor in actors:
            clean_actor = self._clean_text_for_mermaid(actor)
            mermaid += f"    participant {clean_actor}\n"
        
        mermaid += "\n"
        
        # Add interactions
        if interactions:
            for interaction in interactions:
                mermaid += f"    {interaction}\n"
        else:
            # Default interactions
            mermaid += f"    {actors[0]}->>+{actors[1]}: Request\n"
            if len(actors) > 2:
                mermaid += f"    {actors[1]}->>+{actors[2]}: Query\n"
                mermaid += f"    {actors[2]}-->>-{actors[1]}: Response\n"
            mermaid += f"    {actors[1]}-->>-{actors[0]}: Result\n"
        
        return mermaid
    
    def _generate_class_diagram(self, design_doc: DesignDocument) -> str:
        """Generate a class diagram."""
        mermaid = "classDiagram\n"
        
        # Extract classes and relationships
        classes = self._extract_classes(design_doc)
        
        if not classes:
            classes = ["MainClass", "HelperClass", "DataClass"]
        
        # Generate class definitions
        for class_name in classes:
            clean_name = self._clean_text_for_mermaid(class_name)
            mermaid += f"    class {clean_name} {{\n"
            mermaid += f"        +method1()\n"
            mermaid += f"        +method2()\n"
            mermaid += f"    }}\n"
        
        # Add relationships
        for i in range(len(classes) - 1):
            clean_from = self._clean_text_for_mermaid(classes[i])
            clean_to = self._clean_text_for_mermaid(classes[i + 1])
            mermaid += f"    {clean_from} --> {clean_to}\n"
        
        return mermaid
    
    def _generate_generic_graph(self, design_doc: DesignDocument) -> str:
        """Generate a generic graph diagram."""
        mermaid = ["graph LR"]
        
        # Extract key concepts
        concepts = self._extract_key_concepts(design_doc)
        
        if not concepts:
            concepts = self._get_smart_generic_concepts(design_doc.title)
        
        # Add styling
        mermaid.append("")
        mermaid.append("    %% Styling")
        mermaid.append("    classDef input fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000")
        mermaid.append("    classDef processing fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000")
        mermaid.append("    classDef output fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000")
        mermaid.append("    classDef storage fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000")
        mermaid.append("")
        
        # Generate nodes with proper categories
        node_classes = {}
        for i, concept in enumerate(concepts):
            node_id = f"N{i+1}"
            clean_concept = self._clean_text_for_mermaid(concept)
            
            # Categorize concepts
            if i == 0 or any(word in concept.lower() for word in ["input", "user", "client", "request"]):
                mermaid.append(f"    {node_id}([{clean_concept}])")
                node_classes[node_id] = "input"
            elif i == len(concepts)-1 or any(word in concept.lower() for word in ["output", "result", "response"]):
                mermaid.append(f"    {node_id}([{clean_concept}])")
                node_classes[node_id] = "output"
            elif any(word in concept.lower() for word in ["database", "storage", "cache", "store"]):
                mermaid.append(f"    {node_id}[(({clean_concept})])")
                node_classes[node_id] = "storage"
            else:
                mermaid.append(f"    {node_id}[{clean_concept}]")
                node_classes[node_id] = "processing"
        
        mermaid.append("")
        
        # Generate smarter connections
        for i in range(len(concepts) - 1):
            mermaid.append(f"    N{i+1} --> N{i+2}")
        
        # Add some branching if we have enough nodes
        if len(concepts) >= 4:
            mermaid.append(f"    N2 -.-> N{len(concepts)}")  # Dotted line for alternate path
        
        mermaid.append("")
        
        # Apply styling classes
        for node_id, class_name in node_classes.items():
            mermaid.append(f"    class {node_id} {class_name}")
        
        return "\n".join(mermaid)
    
    def _get_smart_generic_concepts(self, title: str) -> List[str]:
        """Get smart default concepts based on the project title.""" 
        title_lower = title.lower()
        
        if 'api' in title_lower:
            return ["Client Request", "API Gateway", "Service Layer", "Data Store", "Response"]
        elif 'system' in title_lower:
            return ["Input", "Validation", "Processing Engine", "Storage", "Output"] 
        else:
            return ["Input", "Processing", "Storage", "Output"]
    
    def _extract_steps(self, design_doc: DesignDocument) -> List[str]:
        """Extract process steps from the design document."""
        steps = []
        
        # Look for numbered steps or sequential indicators
        all_text = " ".join(design_doc.implementation_notes + design_doc.key_decisions)
        
        # Pattern for numbered steps - more specific
        numbered_steps = re.findall(r'\d+[.)]\s*\*?\s*\*?([^.!?\n]+)', all_text)
        if numbered_steps:
            clean_steps = []
            for step in numbered_steps:
                # Clean up the step text
                clean_step = step.strip().rstrip('*').strip()
                if len(clean_step) > 5 and len(clean_step) < 50:  # Reasonable step length
                    clean_steps.append(clean_step)
            if clean_steps:
                steps.extend(clean_steps[:6])
        
        # Pattern for bullet points
        bullet_steps = re.findall(r'[-*]\s+([^.\n]{10,60})', all_text)
        if bullet_steps and not steps:
            clean_bullets = []
            for step in bullet_steps:
                clean_step = step.strip()
                if len(clean_step) > 5:
                    clean_bullets.append(clean_step)
            steps.extend(clean_bullets[:6])
        
        # Pattern for sequential words - but more restrictive  
        if not steps:
            sequential_patterns = [
                r'first[,:]?\s*([^.!\n]{10,40})',
                r'then[,:]?\s*([^.!\n]{10,40})', 
                r'next[,:]?\s*([^.!\n]{10,40})',
                r'finally[,:]?\s*([^.!\n]{10,40})'
            ]
            
            for pattern in sequential_patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 5:
                        steps.append(clean_match)
        
        # Clean and validate steps
        clean_steps = []
        for step in steps:
            step = step.strip()
            # Remove common prefixes and suffixes
            step = re.sub(r'^(the|a|an)\s+', '', step, flags=re.IGNORECASE)
            step = re.sub(r'\s+(and|or|with)$', '', step, flags=re.IGNORECASE)
            
            # Skip if too short, too long, or contains weird patterns
            if (5 <= len(step) <= 50 and 
                not re.search(r'[{}()\[\]]', step) and  # No brackets
                not step.lower().startswith(('hey', 'alright', 'so', 'well', 'but'))):  # No conversational starts
                clean_steps.append(step)
        
        return clean_steps[:6]  # Limit to 6 steps
    
    def _extract_actors(self, design_doc: DesignDocument) -> List[str]:
        """Extract actors/participants from the design document."""
        actors = set()
        all_text = design_doc.description + " " + " ".join(design_doc.implementation_notes)
        
        # Common actor patterns
        actor_patterns = [
            r'\b(user|client|customer|admin|system|server|database|api|service|component)\b'
        ]
        
        for pattern in actor_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            actors.update([match.title() for match in matches])
        
        return list(actors)[:4]  # Limit to 4 actors
    
    def _extract_interactions(self, design_doc: DesignDocument) -> List[str]:
        """Extract interactions for sequence diagrams."""
        # This is a simplified implementation
        # In a real scenario, you'd parse the conversation for interaction patterns
        return []
    
    def _extract_classes(self, design_doc: DesignDocument) -> List[str]:
        """Extract class names from the design document."""
        classes = set()
        all_text = design_doc.description + " " + " ".join(design_doc.implementation_notes)
        
        # Look for class-like terms
        class_patterns = [
            r'\b([A-Z][a-z]+(?:Manager|Service|Controller|Model|Handler|Processor))\b',
            r'\b([A-Z][a-z]+(?:Class|Entity|Object))\b'
        ]
        
        for pattern in class_patterns:
            matches = re.findall(pattern, all_text)
            classes.update(matches)
        
        return list(classes)[:5]  # Limit to 5 classes
    
    def _extract_key_concepts(self, design_doc: DesignDocument) -> List[str]:
        """Extract key concepts for generic diagrams."""
        concepts = []
        
        # Extract from key decisions
        for decision in design_doc.key_decisions:
            # Simple extraction of nouns
            words = decision.split()
            for word in words:
                if len(word) > 4 and word.isalpha() and word[0].isupper():
                    concepts.append(word)
        
        # Remove duplicates and limit
        unique_concepts = []
        for concept in concepts:
            if concept not in unique_concepts:
                unique_concepts.append(concept)
        
        return unique_concepts[:5]  # Limit to 5 concepts
    
    def _clean_text_for_mermaid(self, text: str) -> str:
        """Clean text to be safe for Mermaid diagrams."""
        # Remove special characters and limit length
        cleaned = re.sub(r'[^\w\s-]', '', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Limit length
        if len(cleaned) > 30:
            cleaned = cleaned[:27] + "..."
        
        return cleaned or "Node"