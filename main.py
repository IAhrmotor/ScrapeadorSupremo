"""Main entry point demonstrating the orchestrator agent with hierarchy."""

import asyncio
from agents import OrchestratorAgent, Department, Rank, get_hierarchy
from core.debug import get_debugger, DebugLevel


async def main():
    """Demonstrate the orchestrator agent with hierarchy."""

    # Initialize debug system
    debug = get_debugger()
    debug.set_level(DebugLevel.INFO)  # Change to DEBUG or TRACE for more detail
    debug.show_timestamps = True
    debug.show_file_info = False

    debug.info("main", "Starting ScrapeadorSupremo")

    # Create orchestrator
    orchestrator = OrchestratorAgent()

    print("=" * 60)
    print("SCRAPEADOR SUPREMO - Agent Orchestrator")
    print("=" * 60)

    # Initialize runtime agents
    num_agents = orchestrator.initialize()
    print(f"\nRuntime agents discovered: {num_agents}")

    # Show organizational hierarchy
    print("\n" + orchestrator.print_hierarchy())

    # Demonstrate department routing
    print("\n" + "=" * 60)
    print("ROUTING BY DEPARTMENT")
    print("=" * 60)

    test_cases = [
        (Department.IA, "Create a RAG system with embeddings", Rank.SENIOR),
        (Department.DESARROLLO, "Build a REST API with Python", Rank.SENIOR),
        (Department.CALIDAD, "Review the authentication code", Rank.JUNIOR),
        (Department.DOCUMENTACION, "Generate OpenAPI spec", Rank.JUNIOR),
    ]

    for dept, task, min_rank in test_cases:
        print(f"\n[{dept.name}] Task: {task}")
        agent = orchestrator.route_to_department(task, dept, min_rank)
        if agent:
            print(f"  -> Assigned: {agent.name} [{agent.rank.name}]")
            print(f"     Specialties: {', '.join(agent.specialties[:3])}")
        else:
            print("  -> No suitable agent found")

    # Demonstrate escalation
    print("\n" + "=" * 60)
    print("ESCALATION CHAIN")
    print("=" * 60)

    agent_name = "python-pro"
    print(f"\nStarting from: {agent_name}")
    supervisor = orchestrator.escalate(agent_name)
    level = 1
    while supervisor:
        print(f"  Level {level}: {supervisor.name} [{supervisor.rank.name}]")
        supervisor = orchestrator.escalate(supervisor.name)
        level += 1

    # Demonstrate delegation
    print("\n" + "=" * 60)
    print("DELEGATION")
    print("=" * 60)

    leader = "backend-architect"
    task = "Write async Python code with type hints"
    print(f"\n{leader} delegating: {task}")
    delegate = orchestrator.delegate_down(leader, task)
    if delegate:
        print(f"  -> Delegated to: {delegate.name} [{delegate.rank.name}]")

    # Find experts
    print("\n" + "=" * 60)
    print("FIND EXPERTS")
    print("=" * 60)

    specialties = ["React", "Python", "debugging"]
    for spec in specialties:
        experts = orchestrator.find_expert(spec)
        print(f"\nExperts in '{spec}':")
        for exp in experts:
            print(f"  - {exp.name} [{exp.rank.name}] @ {exp.department.name}")

    # Test runtime agent routing
    print("\n" + "=" * 60)
    print("RUNTIME AGENT ROUTING")
    print("=" * 60)

    test_tasks = [
        "Scrape product data from https://example.com",
        "Organize project folder structure",
        "Analyze data trends and generate report",
    ]

    for task in test_tasks:
        print(f"\nTask: \"{task}\"")
        result = orchestrator.select_agent(task)
        if result:
            agent, confidence = result
            print(f"  -> Runtime Agent: {agent.name} (conf: {confidence:.2f})")

    # Show debug flow report
    debug.info("main", "Demo completed")
    debug.print_flow_report()


if __name__ == "__main__":
    asyncio.run(main())
