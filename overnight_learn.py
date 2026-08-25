"""
Acumen Overnight Knowledge Builder
====================================
Run this before bed. It asks Claude to generate expert knowledge
on dozens of topics and ingests everything into the knowledge base.
Estimated time: 1-2 hours. Estimated cost: ~$3-5 from credits.
"""

import os, time
from dotenv import load_dotenv
load_dotenv(override=True)

from litellm import completion
from acumen.vectordb.ingest import ingest_text
from acumen.memory import MemoryManager

def ask_claude(topic, prompt):
    r = completion(
        model="claude-sonnet-4-20250514",
        messages=[{"role":"user","content":prompt}],
        max_tokens=4000
    )
    return r.choices[0].message.content

topics = [
    ("python_async", "Write an expert guide to Python async programming: asyncio, coroutines, event loops, aiohttp, async generators, task groups, semaphores, and common pitfalls. Include production-ready code examples."),
    ("python_testing", "Write an expert guide to Python testing: pytest, unittest, mocking, fixtures, parametrize, coverage, integration testing, TDD workflow, property-based testing with Hypothesis, and CI/CD test automation. Include examples."),
    ("python_performance", "Write an expert guide to Python performance optimization: profiling (cProfile, line_profiler), memory optimization, caching strategies, multiprocessing vs threading, NumPy vectorization, Cython basics, and database query optimization. Include benchmarks."),
    ("rust_programming", "Write an expert guide to Rust programming: ownership and borrowing, lifetimes, traits, generics, error handling (Result/Option), pattern matching, closures, iterators, concurrency with threads and channels, and async Rust with Tokio. Include code examples."),
    ("go_programming", "Write an expert guide to Go programming: goroutines, channels, select statement, interfaces, error handling patterns, context package, HTTP servers, middleware patterns, testing, and building CLI tools. Include code examples."),
    ("typescript_advanced", "Write an expert guide to advanced TypeScript: type inference, generics, mapped types, conditional types, template literal types, decorators, module augmentation, type guards, utility types, and integrating with React. Include examples."),
    ("react_advanced", "Write an expert guide to advanced React: hooks deep dive (useCallback, useMemo, useReducer, custom hooks), context API, React Server Components, Suspense, error boundaries, performance optimization, state management (Zustand, Redux Toolkit), and testing with React Testing Library."),
    ("system_design", "Write an expert guide to system design: load balancers, caching layers (Redis, Memcached), message queues (Kafka, RabbitMQ), database sharding, CDNs, rate limiting, circuit breakers, service discovery, API gateways, and designing for 1M+ users. Include architecture diagrams in text."),
    ("api_design", "Write an expert guide to API design: REST best practices, GraphQL vs REST, gRPC, API versioning, authentication (OAuth2, JWT), rate limiting, pagination, error handling, documentation (OpenAPI/Swagger), and webhook design. Include examples."),
    ("databases_advanced", "Write an expert guide to advanced databases: SQL optimization, indexing strategies (B-tree, hash, GIN), EXPLAIN ANALYZE, NoSQL patterns (document, key-value, column-family, graph), database replication, connection pooling, migrations, and choosing the right database for your use case."),
    ("devops_complete", "Write an expert guide to DevOps: Docker advanced usage, Kubernetes orchestration, Helm charts, CI/CD with GitHub Actions, infrastructure monitoring, log aggregation (ELK stack), secrets management (Vault), blue-green deployments, canary releases, and incident response. Include config examples."),
    ("security_engineering", "Write an expert guide to security engineering: OWASP Top 10, input validation, SQL injection prevention, XSS prevention, CSRF protection, authentication best practices, encryption at rest and in transit, secrets management, penetration testing basics, and security headers. Include code examples."),
    ("machine_learning_advanced", "Write an expert guide to advanced machine learning: gradient descent variants, regularization techniques, ensemble methods, feature engineering, hyperparameter tuning, cross-validation strategies, handling imbalanced datasets, model interpretability (SHAP, LIME), and MLOps basics. Include Python code with scikit-learn."),
    ("deep_learning", "Write an expert guide to deep learning: neural network architectures (CNN, RNN, LSTM, Transformer), backpropagation, batch normalization, dropout, transfer learning, fine-tuning, attention mechanisms, GANs, autoencoders, and practical tips for training. Include PyTorch code examples."),
    ("nlp_complete", "Write an expert guide to Natural Language Processing: tokenization, word embeddings (Word2Vec, GloVe), transformer architecture explained, BERT and GPT, fine-tuning language models, sentiment analysis, named entity recognition, text classification, RAG (Retrieval Augmented Generation), and prompt engineering. Include code examples."),
    ("data_engineering", "Write an expert guide to data engineering: ETL vs ELT pipelines, data warehousing (Snowflake, BigQuery), data lakes, Apache Spark basics, stream processing (Kafka Streams), data quality frameworks, data modeling (star schema, snowflake schema), dbt, and orchestration with Airflow. Include examples."),
    ("product_management", "Write an expert guide to product management: product discovery, user research methods, jobs-to-be-done framework, prioritization frameworks (RICE, ICE, MoSCoW), roadmap planning, A/B testing, product analytics, stakeholder management, agile vs waterfall, and writing effective PRDs. Include templates."),
    ("fundraising_mastery", "Write an expert guide to startup fundraising: pre-seed to Series C, valuation methods (DCF, comparables, revenue multiples), term sheet anatomy, cap table management, SAFE notes vs convertible notes, investor pitch structure, due diligence preparation, negotiation tactics, and common mistakes. Include examples."),
    ("marketing_growth", "Write an expert guide to tech marketing and growth: content marketing, SEO strategy, paid acquisition (Google Ads, Facebook Ads), email marketing automation, viral loops, referral programs, community building, brand positioning, PLG (product-led growth), and measuring marketing ROI. Include frameworks."),
    ("sales_strategy", "Write an expert guide to B2B sales strategy: sales funnel optimization, lead qualification (BANT, MEDDIC), cold outreach that works, demo best practices, objection handling, pricing negotiation, enterprise sales cycles, channel partnerships, customer success, and building a sales team. Include scripts and templates."),
    ("leadership_management", "Write an expert guide to tech leadership: hiring and retaining engineers, 1-on-1 meeting frameworks, giving effective feedback, managing remote teams, building engineering culture, technical debt negotiation with business, running effective meetings, conflict resolution, and scaling from 10 to 100 people."),
    ("personal_finance", "Write an expert guide to personal finance: budgeting methods, emergency funds, investing basics (stocks, bonds, ETFs, index funds), retirement accounts (401k, IRA, Roth), tax optimization, real estate investing basics, compound interest, dollar cost averaging, and building wealth on a tech salary. Include calculations."),
    ("startup_finance", "Write an expert guide to startup finance: financial modeling, unit economics deep dive, burn rate management, runway extension strategies, revenue recognition, SaaS metrics (MRR, ARR, NRR), cash flow management, financial controls, audit preparation, and board financial reporting. Include spreadsheet formulas."),
    ("economics_essentials", "Write an expert guide to economics essentials: supply and demand, market structures, inflation and monetary policy, fiscal policy, international trade, exchange rates, behavioral economics, game theory basics, cryptocurrency economics, and how economic indicators affect tech businesses."),
    ("technical_writing_pro", "Write an expert guide to professional technical writing: documentation best practices, API documentation, architecture decision records (ADRs), README templates, changelog management, writing RFCs, internal wiki organization, runbook creation, and writing for different technical audiences."),
    ("public_speaking", "Write an expert guide to public speaking for tech professionals: structuring a talk, storytelling techniques, slide design principles, handling Q&A, managing stage fright, conference talk proposals, internal presentations, demo presentations, investor pitches, and virtual presentation tips."),
    ("negotiation_skills", "Write an expert guide to negotiation: preparation framework, BATNA analysis, anchoring techniques, salary negotiation, contract negotiation, vendor negotiation, win-win strategies, handling difficult negotiators, cross-cultural negotiation, and negotiating equity in startups. Include scripts and scenarios."),
    ("web3_advanced", "Write an expert guide to advanced Web3: Layer 2 scaling solutions (Optimistic rollups, ZK rollups), cross-chain bridges, MEV (Miner Extractable Value), DAO governance models, token engineering, on-chain analytics, DeFi protocol design, NFT utility beyond art, and the future of decentralized identity."),
    ("ai_agents", "Write an expert guide to AI agent systems: agent architectures, tool use, chain-of-thought reasoning, ReAct pattern, multi-agent coordination, memory systems for agents, evaluation frameworks, safety and alignment, function calling, and building production agent systems. Include code patterns."),
    ("edge_computing", "Write an expert guide to edge computing: edge vs cloud, IoT architectures, edge AI inference, 5G and edge computing, content delivery at the edge, edge databases, security at the edge, Kubernetes at the edge (K3s), real-time processing, and use cases across industries."),
    ("cloud_dag_architecture", "Write an expert blueprint for building a cloud data storage system with DAG-based orchestration. Cover: overall system architecture, how the DAG scheduler coordinates storage operations (replication, sharding, compaction, garbage collection), node communication protocols, data flow diagrams described in text, and how each component connects. This should be detailed enough that an AI agent could use it as instructions to build the system."),
    ("cloud_dag_storage_engine", "Write complete, production-ready Python code for a cloud storage engine with: a Storage Node class that handles PUT/GET/DELETE operations, consistent hashing for data distribution, write-ahead logging for durability, a replication manager that copies data to N nodes, health checking, and a REST API using FastAPI. Include every import, every class, every function. The code should be copy-paste ready."),
    ("cloud_dag_scheduler_code", "Write complete, production-ready Rust code for a DAG scheduler that orchestrates cloud storage operations: task dependency resolution, topological sorting, parallel task dispatch via channels, retry logic with exponential backoff, priority queues, dead letter handling, and a gRPC server interface. Include full Cargo.toml and complete main.rs. The code should be copy-paste ready."),
    ("cloud_dag_worker_code", "Write complete, production-ready Go code for DAG task workers that execute cloud storage operations: a worker pool with configurable concurrency, HTTP endpoints for task submission and status, goroutine-based execution, timeout handling, result caching, metrics collection, and graceful shutdown. Include full go.mod and complete main.go. The code should be copy-paste ready."),
    ("cloud_dag_metadata", "Write complete Python code for a metadata service for a cloud storage DAG system: a metadata database using SQLite that tracks file locations across nodes, chunk-to-node mappings, replication status, file versioning, garbage collection tracking, and a query API. Include schema definitions, all CRUD operations, and a FastAPI interface. Code should be copy-paste ready."),
    ("cloud_dag_networking", "Write an expert guide to building the networking layer for a cloud storage DAG system: peer-to-peer node discovery, gossip protocol for cluster membership, heartbeat monitoring, split-brain prevention, data transfer protocols (chunked streaming), TLS encryption between nodes, and load balancing incoming requests. Include Python and Go code examples."),
    ("cloud_dag_testing_deploy", "Write an expert guide to testing and deploying a cloud storage DAG system: unit testing each component, integration testing the full pipeline, chaos engineering (simulating node failures), performance benchmarking, Docker Compose for local multi-node testing, Kubernetes deployment manifests, monitoring with Prometheus and Grafana, and alerting rules. Include all config files and test code."),
    ("cloud_dag_step_by_step", "Write a complete step-by-step tutorial for building a cloud data storage system with DAG orchestration from absolute scratch. Number every step. Include: 1) Project setup and directory structure, 2) Building the storage engine, 3) Building the DAG scheduler, 4) Building the workers, 5) Building the metadata service, 6) Connecting everything together, 7) Testing, 8) Deployment. For each step include the exact files to create, the exact code to write, and the exact commands to run. An AI should be able to follow these instructions and build the entire system autonomously."),
]

print("=" * 60)
print("  ACUMEN OVERNIGHT KNOWLEDGE BUILDER")
print("=" * 60)
print(f"\nTopics to learn: {len(topics)}")
print(f"Estimated time: 1-2 hours")
print(f"Estimated cost: ~$3-5 in Claude API credits")
print()

memory = MemoryManager()
before = memory.knowledge_count()
total_chunks = 0
errors = 0
start_time = time.time()

for i, (topic_id, prompt) in enumerate(topics):
    print(f"[{i+1}/{len(topics)}] {topic_id}...", end=" ", flush=True)
    try:
        content = ask_claude(topic_id, prompt)
        chunks = ingest_text(content, topic=topic_id, source="claude_overnight")
        total_chunks += chunks
        print(f"OK ({chunks} chunks)")
        time.sleep(1)
    except Exception as e:
        errors += 1
        print(f"ERROR: {str(e)[:80]}")
        time.sleep(5)

elapsed = (time.time() - start_time) / 60
after = memory.knowledge_count()

print()
print("=" * 60)
print("  OVERNIGHT LEARNING COMPLETE!")
print("=" * 60)
print(f"  Knowledge base: {before} -> {after} docs")
print(f"  New chunks: {total_chunks}")
print(f"  Errors: {errors}")
print(f"  Time: {elapsed:.1f} minutes")
print(f"  Topics covered: {len(topics) - errors}")
print("=" * 60)