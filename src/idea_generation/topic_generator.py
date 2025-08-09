"""Generate design topics from various sources.

Enhancements:
- Dynamic keyword bias (reads config each call so env overrides work)
- Avoid immediate repetition of the last used topic when possible
- Weighted random selection among top scored candidates instead of uniform in fixed slice
"""

import random
import os
import json
from typing import List, Dict, Optional
from datetime import datetime


from ..config import config


class TopicGenerator:
    """Generates design topics for AI conversations."""
    
    def __init__(self):
        self.predefined_topics = [
            {
                "topic": "Design a distributed caching system",
                "context": "Handle millions of requests per second with sub-millisecond latency",
                "category": "infrastructure"
            },
            {
                "topic": "Create a real-time collaborative code editor",
                "context": "Support multiple programming languages with live syntax highlighting",
                "category": "developer-tools"
            },
            {
                "topic": "Design a microservices monitoring platform",
                "context": "Track health, performance, and dependencies across 100+ services",
                "category": "observability"
            },
            {
                "topic": "Build a serverless image processing pipeline",
                "context": "Process millions of images daily with various transformations",
                "category": "media-processing"
            },
            {
                "topic": "Design a secure multi-tenant SaaS platform",
                "context": "Ensure data isolation and compliance for enterprise customers",
                "category": "saas"
            },
            {
                "topic": "Create a real-time fraud detection system",
                "context": "Analyze transactions in real-time with machine learning",
                "category": "fintech"
            },
            {
                "topic": "Design a content delivery network architecture",
                "context": "Serve content globally with 99.99% uptime and edge caching",
                "category": "infrastructure"
            },
            {
                "topic": "Build a GraphQL API gateway",
                "context": "Unify multiple REST APIs behind a single GraphQL interface",
                "category": "api-design"
            },
            {
                "topic": "Design a blockchain-based supply chain tracker",
                "context": "Ensure transparency and authenticity from manufacturer to consumer",
                "category": "blockchain"
            },
            {
                "topic": "Create a progressive web app for offline functionality",
                "context": "Work seamlessly without internet connection and sync when online",
                "category": "frontend"
            },
            {
                "topic": "Design a machine learning model deployment platform",
                "context": "Deploy, version, and monitor ML models at scale",
                "category": "ml-ops"
            },
            {
                "topic": "Build a real-time chat application with encryption",
                "context": "Support millions of concurrent users with end-to-end encryption",
                "category": "communication"
            },
            {
                "topic": "Design a container orchestration strategy",
                "context": "Manage containers across hybrid cloud environments",
                "category": "devops"
            },
            {
                "topic": "Create a distributed logging system",
                "context": "Collect, process, and search logs from thousands of services",
                "category": "observability"
            },
            {
                "topic": "Design a recommendation engine architecture",
                "context": "Provide personalized recommendations for e-commerce platform",
                "category": "machine-learning"
            }
        ]
        
        self.trending_contexts = [
            "Consider AI/ML integration opportunities",
            "Focus on sustainability and green computing",
            "Prioritize accessibility and inclusive design",
            "Design for edge computing and IoT devices",
            "Consider Web3 and decentralized architectures",
            "Focus on zero-trust security principles",
            "Design for multi-cloud and hybrid environments",
            "Prioritize developer experience and productivity",
            "Consider real-time and event-driven architectures",
            "Focus on cost optimization and resource efficiency"
        ]
    
    def _apply_keyword_bias(self, candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Return candidates reordered giving preference to IDEA_KEYWORDS matches."""
        if not config.idea_keywords:
            return candidates
        keywords = [k.lower() for k in config.idea_keywords]
        scored = []
        for t in candidates:
            text = (t["topic"] + " " + t.get("context", "")).lower()
            score = sum(1 for k in keywords if k in text)
            # Add small random jitter to avoid deterministic always-first when equal
            t = dict(t)  # shallow copy to avoid mutating original list
            t["bias_score"] = score
            scored.append((score + random.random() * 0.01, t))
        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored]

    def _get_last_topic(self) -> Optional[str]:
        """Try to read the most recent project's topic to reduce repetition."""
        try:
            projects_dir = config.projects_dir
            if not os.path.isdir(projects_dir):
                return None
            entries = [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
            if not entries:
                return None
            latest = sorted(entries)[-1]
            session_path = os.path.join(projects_dir, latest, 'session.json')
            if not os.path.isfile(session_path):
                return None
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('config', {}).get('topic') or data.get('topic')
        except Exception:
            return None

    def get_random_topic(self) -> Dict[str, str]:
        """Get a random topic from predefined list, with keyword bias, avoiding immediate repeats."""
        candidates = self._apply_keyword_bias(self.predefined_topics.copy())
        if not candidates:
            raise ValueError("No topics available")

        # If any have positive bias_score, restrict selection to those
        positive = [c for c in candidates if c.get("bias_score", 0) > 0]
        selection_pool = positive if positive else candidates

        # Compute weighted probabilities based on relative score rank (earlier = higher score)
        weights = [1.0 / (i + 1) for i in range(len(selection_pool))]  # simple harmonic decay
        total_w = sum(weights)
        rnd = random.random() * total_w
        cumulative = 0.0
        chosen = selection_pool[-1]
        for c, w in zip(selection_pool, weights):
            cumulative += w
            if rnd <= cumulative:
                chosen = c
                break

        last_topic = self._get_last_topic()
        if last_topic and chosen["topic"] == last_topic:
            # Try to pick an alternative with same or next best weighting
            alt = [c for c in selection_pool if c["topic"] != last_topic]
            if alt:
                chosen = random.choice(alt[: min(5, len(alt))])

        # Optionally add a trending context
        if random.random() < 0.3:
            additional_context = random.choice(self.trending_contexts)
            chosen["context"] += f". {additional_context}"
        return chosen
    
    def get_topic_by_category(self, category: str) -> Optional[Dict[str, str]]:
        """Get a random topic from a specific category."""
        category_topics = [
            topic for topic in self.predefined_topics 
            if topic["category"] == category
        ]
        
        if not category_topics:
            return None
        
        return random.choice(category_topics)
    
    def get_daily_topic(self) -> Dict[str, str]:
        """Get a topic based on the day of the week."""
        day_of_week = datetime.now().weekday()

        day_categories = {
            0: "infrastructure",
            1: "api-design",
            2: "frontend",
            3: "devops",
            4: "machine-learning",
            5: "saas",
            6: "fintech"
        }
        preferred_category = day_categories.get(day_of_week)
        topic = self.get_topic_by_category(preferred_category)

        if not topic:
            topic = self.get_random_topic()

        if config.idea_keywords and topic:
            biased_all = self._apply_keyword_bias(self.predefined_topics.copy())
            filtered = [t for t in biased_all if t["category"] == preferred_category]
            if filtered:
                topic = filtered[0]
            else:
                topic = biased_all[0]
        return topic
    
    def get_trending_topic(self) -> Dict[str, str]:
        """Get a topic with trending technology focus."""
        topic = self.get_random_topic()
        trending_context = random.choice(self.trending_contexts)
        
        topic["context"] += f". {trending_context}"
        return topic
    
    def list_categories(self) -> List[str]:
        """List all available topic categories."""
        categories = set(topic["category"] for topic in self.predefined_topics)
        return sorted(list(categories))
    
    def get_topics_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get all topics in a specific category."""
        return [
            topic for topic in self.predefined_topics 
            if topic["category"] == category
        ]