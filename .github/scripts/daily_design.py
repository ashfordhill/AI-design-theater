import asyncio
from src.main import AIDesignTheater
from src.idea_generation.topic_generator import TopicGenerator

async def main():
    tg = TopicGenerator()
    topic_data = tg.get_daily_topic()
    topic = topic_data['topic']
    context = topic_data.get('context')
    theater = AIDesignTheater()
    project_dir = await theater.run_design_session(
        topic=topic,
        context=context,
        max_turns=18,
        max_duration_minutes=25,
    )
    with open('daily_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f"Topic: {topic}\n")
        if context:
            f.write(f"Context: {context}\n")
        f.write(f"Project: {project_dir}\n")

if __name__ == '__main__':
    asyncio.run(main())
