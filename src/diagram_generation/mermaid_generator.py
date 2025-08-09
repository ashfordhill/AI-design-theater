"""Mermaid diagram generation from design documents."""

import re
from typing import List, Dict, Any, Optional
from ..models import DesignDocument


class MermaidGenerator:
    """Generates Mermaid diagrams from design conversations."""
    
    def generate_architecture_diagram(self, design_doc: DesignDocument, detail_level: int = 5) -> str:
        """Generate a Mermaid architecture diagram from the design document.

        detail_level (1-10) influences richness; >6 attempts component style.
        """
        content = self._get_all_content(design_doc)
        if detail_level >= 7:
            return self._generate_component_graph(design_doc, detail_level)
        if self._is_flowchart_suitable(content):
            return self._generate_flowchart(design_doc)
        if self._is_sequence_suitable(content):
            return self._generate_sequence_diagram(design_doc)
        if self._is_class_suitable(content):
            return self._generate_class_diagram(design_doc)
        return self._generate_generic_graph(design_doc)

    def _generate_component_graph(self, design_doc: DesignDocument, detail_level: int) -> str:
        """Generate a richer software architecture component diagram (graph LR)."""
        mermaid = ["graph LR"]
        # Basic inferred components
        base_components = [
            ("Client", "End User / UI"),
            ("APIGW", "API Gateway"),
            ("Auth", "Auth / IAM"),
            ("SvcA", "Core Service"),
            ("SvcB", "Aux Service"),
            ("Queue", "Event / Queue"),
            ("Cache", "Cache Layer"),
            ("DB", "Primary DB"),
            ("Obs", "Observability")
        ]
        # Add more if high detail
        if detail_level >= 9:
            base_components += [
                ("CDN", "CDN / Edge"),
                ("ObjStore", "Object Storage"),
                ("Search", "Search Index"),
                ("ML", "ML Inference"),
                ("Analytics", "Analytics Sink")
            ]
        # Emit nodes
        for ident, label in base_components[: (len(base_components) if detail_level >= 9 else 9)]:
            mermaid.append(f"    {ident}[{label}]")
        # Edges (simplified flow)
        edges = [
            ("Client", "CDN" if any(c[0]=="CDN" for c in base_components) else "APIGW"),
            ("CDN" if any(c[0]=="CDN" for c in base_components) else "APIGW", "APIGW"),
            ("APIGW", "Auth"),
            ("APIGW", "SvcA"),
            ("APIGW", "SvcB"),
            ("SvcA", "Cache"),
            ("SvcA", "Queue"),
            ("SvcA", "DB"),
            ("SvcB", "DB"),
            ("Queue", "SvcB"),
            ("SvcA", "Obs"),
            ("SvcB", "Obs"),
        ]
        if detail_level >= 9:
            edges += [
                ("APIGW", "ML"),
                ("SvcA", "Search"),
                ("SvcB", "ObjStore"),
                ("DB", "Analytics"),
                ("Queue", "Analytics")
            ]
        # Deduplicate edges
        seen = set()
        for a,b in edges:
            if (a,b) in seen:
                continue
            seen.add((a,b))
            mermaid.append(f"    {a} --> {b}")
        return "\n".join(mermaid)
    
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
        mermaid = "flowchart TD\n"
        
        # Extract steps from implementation notes and decisions
        steps = self._extract_steps(design_doc)
        
        if not steps:
            steps = ["Start", "Process", "Decision", "End"]
        
        # Generate nodes
        for i, step in enumerate(steps):
            node_id = f"A{i+1}"
            clean_step = self._clean_text_for_mermaid(step)
            
            if i == 0:
                mermaid += f"    {node_id}[{clean_step}]\n"
            elif i == len(steps) - 1:
                mermaid += f"    {node_id}[{clean_step}]\n"
            elif "decision" in step.lower() or "choose" in step.lower():
                mermaid += f"    {node_id}{{{clean_step}}}\n"
            else:
                mermaid += f"    {node_id}[{clean_step}]\n"
        
        # Generate connections
        for i in range(len(steps) - 1):
            mermaid += f"    A{i+1} --> A{i+2}\n"
        
        return mermaid
    
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
        mermaid = "graph TD\n"
        
        # Extract key concepts
        concepts = self._extract_key_concepts(design_doc)
        
        if not concepts:
            concepts = ["Input", "Processing", "Output"]
        
        # Generate nodes
        for i, concept in enumerate(concepts):
            node_id = f"N{i+1}"
            clean_concept = self._clean_text_for_mermaid(concept)
            mermaid += f"    {node_id}[{clean_concept}]\n"
        
        # Generate connections
        for i in range(len(concepts) - 1):
            mermaid += f"    N{i+1} --> N{i+2}\n"
        
        return mermaid
    
    def _extract_steps(self, design_doc: DesignDocument) -> List[str]:
        """Extract process steps from the design document."""
        steps = []
        
        # Look for numbered steps or sequential indicators
        all_text = " ".join(design_doc.implementation_notes + design_doc.key_decisions)
        
        # Pattern for numbered steps
        numbered_steps = re.findall(r'\d+[.)]\s*([^.]+)', all_text)
        if numbered_steps:
            steps.extend(numbered_steps)
        
        # Pattern for sequential words
        sequential_patterns = [
            r'first[,:]?\s*([^.]+)',
            r'then[,:]?\s*([^.]+)',
            r'next[,:]?\s*([^.]+)',
            r'finally[,:]?\s*([^.]+)'
        ]
        
        for pattern in sequential_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            steps.extend(matches)
        
        return [step.strip() for step in steps if step.strip()][:6]  # Limit to 6 steps
    
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