"""
Acumen Maximum Knowledge Pack
================================
Smart download - skips topics already in knowledge base.
Only downloads what's NEW. Includes everything needed to approach
Claude/ChatGPT level knowledge.
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

def topic_exists(memory, search_term):
    results = memory.search_knowledge(search_term, n=1)
    if results and float(results[0]["relevance"].replace("%","")) > 50:
        return True
    return False

topics = [
    # ============================================
    # PROGRAMMING LANGUAGES DEEP (20)
    # ============================================
    ("python_metaprogramming", "metaclasses descriptors __init_subclass__", "Write an expert guide to Python metaprogramming: metaclasses, class decorators, descriptors, __init_subclass__, __set_name__, dynamic class creation, monkey patching, import hooks, AST manipulation, and building a plugin system. Include complete code."),
    ("python_c_extensions", "Python C extensions ctypes cffi Cython", "Write an expert guide to Python C extensions: ctypes, cffi, Cython, writing C extensions with Python.h, NumPy C API, memory management, building extensions, and performance comparison. Include complete code for each approach."),
    ("python_concurrency_deep", "asyncio uvloop trio structured concurrency event loop", "Write an expert guide to advanced Python concurrency: asyncio internals, event loop customization, uvloop, trio, structured concurrency, async generators, async context managers, multiprocessing with shared memory, and building a high-performance async server. Include code."),
    ("python_internals", "CPython bytecode GIL reference counting garbage collection", "Write an expert guide to Python internals: CPython architecture, bytecode compilation, the GIL, memory management (reference counting, garbage collection), object model, descriptor protocol, metaclasses, slots, and how Python executes code. Include dis module examples."),
    ("python_data_science", "NumPy Pandas Matplotlib Seaborn data cleaning", "Write an expert guide to Python for data science: NumPy (arrays, broadcasting, linear algebra), Pandas (DataFrames, groupby, merge, pivot, time series), Matplotlib and Seaborn visualization, Scipy, and data cleaning workflows. Include complete code."),
    ("python_web_scraping", "web scraping BeautifulSoup Selenium Scrapy Playwright", "Write an expert guide to Python web scraping: requests, BeautifulSoup, Selenium, Playwright, Scrapy framework, handling pagination, anti-scraping measures, rotating proxies, parsing JSON APIs, and storing scraped data. Include complete examples."),
    ("python_automation", "Python automation Excel PDF email scheduling CLI", "Write an expert guide to Python automation: file operations (shutil, pathlib), Excel (openpyxl), PDF (PyPDF2, reportlab), email (smtplib), scheduling tasks, Selenium, PyAutoGUI, and building CLI tools with Click. Include examples."),
    ("rust_ownership_mastery", "Rust borrow checker lifetime annotations Pin interior mutability", "Write an expert guide to mastering Rust ownership: every borrow checker error explained with fixes, lifetime annotations, self-referential structs (Pin), interior mutability, Cow, phantom data, variance, and advanced lifetime patterns. Include 30+ examples."),
    ("rust_unsafe_ffi", "unsafe Rust FFI raw pointers transmute PyO3 C interop", "Write an expert guide to unsafe Rust and FFI: when unsafe is necessary, raw pointers, transmute, unions, calling C from Rust, calling Rust from C, calling Rust from Python (PyO3), memory layout, and proving unsafe code is sound. Include examples."),
    ("rust_wasm", "Rust WebAssembly wasm-pack wasm-bindgen WASI browser", "Write an expert guide to Rust and WebAssembly: wasm-pack, wasm-bindgen, building browser modules, performance vs JavaScript, DOM manipulation from Rust, shared memory, WASI, and building a complete web component. Include code."),
    ("cpp_modern", "modern C++ smart pointers concepts coroutines modules ranges", "Write an expert guide to modern C++ (C++17/20/23): smart pointers, move semantics, RAII, templates and concepts, ranges, coroutines, modules, constexpr, structured bindings, std::optional/variant/any. Include code examples."),
    ("java_modern", "modern Java records sealed classes virtual threads Spring Boot", "Write an expert guide to modern Java (17+): records, sealed classes, pattern matching, virtual threads (Loom), text blocks, switch expressions, modules, Stream API advanced, CompletableFuture, and Spring Boot 3 microservices. Include code."),
    ("csharp_dotnet", "C# .NET async LINQ Entity Framework Blazor SignalR", "Write an expert guide to C# and .NET: async/await, LINQ, generics, delegates, dependency injection, Entity Framework Core, ASP.NET Core, SignalR, gRPC, Blazor, and building a full-stack application. Include code."),
    ("elixir_erlang", "Elixir BEAM OTP GenServer Phoenix LiveView Ecto", "Write an expert guide to Elixir and BEAM: processes, message passing, OTP (GenServer, Supervisor), fault tolerance, hot code reloading, Phoenix, LiveView, Ecto, distributed Elixir, and building a real-time app. Include code."),
    ("haskell_functional", "Haskell monads type classes functors applicatives algebraic", "Write an expert guide to Haskell: type system, type classes, monads (Maybe, IO, State, Reader, Writer), monad transformers, functors, applicatives, lazy evaluation, algebraic data types, and building a real application. Include code."),
    ("scala_jvm", "Scala case classes pattern matching Akka ZIO Cats Spark", "Write an expert guide to Scala: type system, case classes, pattern matching, traits, implicits, Futures, Akka actors, ZIO effects, Cats library, Spark with Scala, and building distributed applications. Include code."),
    ("vue_complete", "Vue 3 Composition API Pinia reactivity watchers", "Write an expert guide to Vue.js 3: Composition API, reactivity system, computed properties, watchers, lifecycle hooks, component communication, Pinia, Vue Router, testing, and building a complete app. Include code."),
    ("svelte_complete", "Svelte SvelteKit reactive stores transitions animations", "Write an expert guide to Svelte and SvelteKit: reactive declarations, stores, transitions, SvelteKit routing, load functions, form actions, SSR, API endpoints, and deployment. Include complete code."),
    ("kotlin_multiplatform", "Kotlin Multiplatform Compose KMM Ktor", "Write an expert guide to Kotlin Multiplatform: shared logic, platform-specific code, Kotlin/Native, Kotlin/JS, Compose Multiplatform, Ktor, serialization, Koin, and building a cross-platform app. Include code."),
    ("tauri_desktop", "Tauri Rust desktop app IPC plugins packaging", "Write an expert guide to Tauri desktop apps: Rust backend, web frontend, IPC commands, system tray, file dialogs, auto-updates, plugins, security, packaging, and comparison with Electron. Include code."),

    # ============================================
    # JAVASCRIPT ENGINE & PATTERNS (6)
    # ============================================
    ("javascript_engine", "V8 JIT compilation hidden classes event loop microtasks", "Write an expert guide to JavaScript engine internals: V8 architecture, JIT compilation, hidden classes, inline caching, garbage collection, event loop (microtasks vs macrotasks), call stack, memory heap, and performance optimization. Include examples."),
    ("javascript_patterns", "JavaScript design patterns module observer factory proxy", "Write an expert guide to JavaScript design patterns: module, revealing module, observer, pub/sub, mediator, factory, singleton, proxy, decorator, facade, command, and strategy. Include modern ES6+ implementations."),
    ("node_microservices", "Node.js microservices gRPC service discovery circuit breaker", "Write an expert guide to Node.js microservices: service decomposition, communication (REST, gRPC, queues), API gateway, service discovery, circuit breaker, distributed tracing, Docker, and Kubernetes deployment. Include code."),
    ("deno_bun_runtimes", "Deno Bun JavaScript runtimes permissions bundler", "Write an expert guide to Deno and Bun: Deno permissions and built-in tools, Bun speed and bundler, comparing Node vs Deno vs Bun, migration strategies, and when to use each. Include practical examples."),
    ("javascript_security", "JavaScript security XSS CSRF prototype pollution CSP", "Write an expert guide to JavaScript security: XSS prevention, CSRF protection, prototype pollution, Content Security Policy, secure cookies, DOM clobbering, supply chain attacks, and building secure JavaScript applications. Include code."),
    ("webassembly_deep", "WebAssembly WASM WASI component model threads SIMD", "Write an expert guide to WebAssembly: binary format, text format (WAT), WASI, component model, threads, SIMD, memory management, interfacing with JavaScript, performance optimization, and real-world use cases. Include examples."),

    # ============================================
    # SYSTEM DESIGN PATTERNS (14)
    # ============================================
    ("event_driven_architecture", "event sourcing CQRS event stores projections snapshots", "Write an expert guide to event-driven architecture: event sourcing, CQRS, event stores, projections, snapshots, eventual consistency, compensating transactions, event schema evolution, and building a complete event-driven system. Include code."),
    ("caching_strategies", "cache invalidation distributed caching Redis stampede write-behind", "Write an expert guide to caching: cache-aside, read-through, write-through, write-behind, invalidation strategies, distributed caching, consistency, warming, multi-layer caching, stampede prevention, and Redis implementation. Include code."),
    ("search_engine_design", "inverted index TF-IDF BM25 autocomplete spell correction", "Write an expert guide to search engine design: inverted indexes, tokenization, TF-IDF, BM25, faceted search, autocomplete, spell correction, distributed search, near-real-time indexing, and building one from scratch. Include code."),
    ("real_time_systems", "WebSocket SSE CRDT OT real-time collaboration presence", "Write an expert guide to real-time systems: WebSocket, Server-Sent Events, long polling, real-time databases, presence, typing indicators, CRDT, OT, and building a real-time chat system. Include code."),
    ("payment_systems", "payment processing Stripe PCI DSS subscriptions idempotency", "Write an expert guide to payment systems: processing flow, PCI DSS, Stripe integration, webhooks, idempotency, refunds, disputes, multi-currency, and building a billing system. Include code."),
    ("notification_systems", "push notifications FCM APNs email SMS multi-channel", "Write an expert guide to notification systems: push (FCM, APNs), email, SMS, in-app, preferences, templating, rate limiting, delivery tracking, and building a multi-channel system. Include code."),
    ("feature_flag_systems", "feature flags A/B testing percentage rollout kill switch", "Write an expert guide to feature flags: boolean flags, percentage rollouts, targeting, A/B testing, kill switches, lifecycle management, and building a feature flag system from scratch. Include code."),
    ("authentication_systems", "authentication OAuth2 PKCE JWT WebAuthn passwordless MFA", "Write an expert guide to authentication: session-based, JWT, OAuth2 flows (authorization code, PKCE), OpenID Connect, SAML, passwordless (WebAuthn, magic links), MFA, and building a complete auth system. Include code."),
    ("file_storage_systems", "object storage content-addressable chunking CDN presigned", "Write an expert guide to file storage design: object storage architecture, content-addressable storage, chunking, deduplication, CDN integration, presigned URLs, image processing, video transcoding, and building a storage service. Include code."),
    ("logging_systems", "structured logging correlation IDs distributed tracing aggregation", "Write an expert guide to logging systems: structured logging, log levels, correlation IDs, distributed tracing, log aggregation (ELK, Loki), retention, alerting, audit logging, and building a centralized logging system. Include code."),
    ("api_gateway_patterns", "API gateway routing auth rate limiting circuit breaker caching", "Write an expert guide to API gateway patterns: routing, authentication, rate limiting, request transformation, circuit breaking, caching, logging, versioning, and building a custom API gateway. Include code."),
    ("message_queue_patterns", "message queue pub/sub competing consumers dead letter exactly-once", "Write an expert guide to message queue patterns: point-to-point, pub/sub, request-reply, competing consumers, routing, dead letter queues, ordering, exactly-once delivery, and comparing RabbitMQ, Kafka, SQS, NATS. Include code."),
    ("database_scaling", "database scaling sharding read replicas partitioning NewSQL", "Write an expert guide to database scaling: vertical vs horizontal, read replicas, sharding strategies, connection pooling, query optimization, materialized views, database proxies, NewSQL (CockroachDB, TiDB), and multi-region databases."),
    ("ci_cd_advanced", "CI/CD pipeline parallelization artifacts deployment strategies GitOps", "Write an expert guide to advanced CI/CD: pipeline design, parallelization, caching, artifact management, deployment strategies (blue-green, canary, rolling), environment management, security scanning, and GitHub Actions/GitLab CI. Include configs."),

    # ============================================
    # CLOUD ADVANCED (10)
    # ============================================
    ("aws_advanced", "AWS Step Functions EventBridge CDK Well-Architected cost", "Write an expert guide to advanced AWS: Step Functions, EventBridge, AppSync, Cognito, WAF, Secrets Manager, CDK, Well-Architected Framework, cost optimization, reserved and spot instances. Include architecture patterns."),
    ("kubernetes_operators", "Kubernetes operators CRD controller kubebuilder reconciliation", "Write an expert guide to Kubernetes operators: CRDs, controller pattern, Operator SDK, kubebuilder, reconciliation loop, status subresource, finalizers, webhooks, and building a complete operator. Include Go code."),
    ("service_mesh_deep", "service mesh Envoy Istio mTLS traffic management fault injection", "Write an expert guide to service mesh: Envoy internals, Istio architecture, traffic management, mutual TLS, observability, fault injection, rate limiting, retries, circuit breaking, and implementation. Include configuration."),
    ("gitops_practices", "GitOps ArgoCD Flux repository structure secrets sealed", "Write an expert guide to GitOps: principles, ArgoCD, Flux CD, repository structure, application-of-apps, secrets management (Sealed Secrets, SOPS), progressive delivery, and implementing GitOps for production. Include examples."),
    ("chaos_engineering", "chaos engineering Chaos Monkey Litmus blast radius game days", "Write an expert guide to chaos engineering: principles, Chaos Monkey, Litmus, steady-state hypothesis, blast radius, game days, production chaos, network chaos, and building a chaos engineering program. Include experiments."),
    ("platform_engineering", "platform engineering internal developer platform Backstage golden paths", "Write an expert guide to platform engineering: internal developer platforms, golden paths, self-service infrastructure, developer experience metrics, Backstage, platform APIs, and building an internal platform. Include architecture."),
    ("disaster_recovery", "disaster recovery RPO RTO multi-region failover backup 3-2-1", "Write an expert guide to disaster recovery: RPO/RTO planning, backup strategies (3-2-1), multi-region architecture, failover automation, DNS failover, database replication for DR, testing DR plans, and building a DR strategy."),
    ("cost_optimization_cloud", "cloud cost optimization right-sizing reserved spot FinOps", "Write an expert guide to cloud cost optimization: right-sizing, reserved instances, spot instances, auto-scaling optimization, storage tiering, data transfer optimization, FinOps practices, and reducing cloud bills by 50%."),
    ("container_security", "container security image scanning Trivy non-root Falco SLSA", "Write an expert guide to container security: image scanning (Trivy), minimal base images, non-root containers, read-only filesystems, network policies, pod security, runtime security (Falco), supply chain (SLSA), and building a secure pipeline."),
    ("edge_infrastructure", "edge computing Cloudflare Workers edge databases Turso", "Write an expert guide to edge infrastructure: edge platforms (AWS Wavelength, Cloudflare Workers), edge databases (Turso, SQLite at edge), edge caching, edge AI, IoT gateways, and building edge applications. Include examples."),

    # ============================================
    # DATABASES DEEP (10)
    # ============================================
    ("database_internals", "B-tree LSM-tree WAL MVCC buffer pool query optimizer", "Write an expert guide to database internals: B-tree and LSM-tree storage engines, write-ahead logging, MVCC, buffer pool management, query optimization (cost-based), join algorithms, and building a simple database. Include code."),
    ("distributed_databases", "distributed database Raft partitioning Spanner CockroachDB", "Write an expert guide to distributed databases: partitioning, replication, consensus (Raft in detail), distributed transactions, clock synchronization, conflict resolution, CockroachDB and Spanner architecture. Include examples."),
    ("neo4j_graph_db", "Neo4j graph database Cypher PageRank community detection", "Write an expert guide to Neo4j and graph databases: property graph model, Cypher language, graph algorithms (shortest path, PageRank, community detection), modeling, performance, and real-world use cases. Include examples."),
    ("timeseries_databases", "time series InfluxDB TimescaleDB Prometheus downsampling", "Write an expert guide to time-series databases: InfluxDB, TimescaleDB, Prometheus TSDB, retention policies, downsampling, continuous queries, Grafana dashboards, alerting, and choosing the right TSDB. Include examples."),
    ("streaming_databases", "streaming database Materialize Flink SQL real-time analytics", "Write an expert guide to streaming databases: Materialize, RisingWave, Flink SQL, real-time aggregations, sliding windows, watermarks, late data handling, and building a real-time analytics pipeline. Include code."),
    ("apache_spark_advanced", "Spark catalyst tungsten adaptive partition pruning PySpark", "Write an expert guide to advanced Spark: catalyst optimizer, tungsten engine, adaptive query execution, dynamic partition pruning, Spark on Kubernetes, Delta Lake, Structured Streaming, and performance tuning. Include PySpark code."),
    ("data_lake_advanced", "Delta Lake Iceberg Hudi lakehouse medallion architecture", "Write an expert guide to data lakes: Delta Lake (ACID, time travel), Apache Iceberg (hidden partitioning), Apache Hudi (upserts), lakehouse architecture, and choosing between formats. Include examples."),
    ("data_quality_governance", "data quality Great Expectations data contracts observability lineage", "Write an expert guide to data quality and governance: profiling, validation (Great Expectations), data contracts, schema evolution, observability, lineage, freshness, and building a data quality framework. Include code."),
    ("etl_cdc_patterns", "ETL CDC Debezium Change Data Capture incremental upsert", "Write an expert guide to ETL/CDC patterns: change data capture (Debezium), log-based CDC, incremental loads, merge/upsert, deduplication, late-arriving data, and building a complete CDC pipeline. Include code."),
    ("metadata_management", "metadata catalog DataHub Amundsen lineage discovery", "Write an expert guide to metadata management: data catalogs (DataHub, Amundsen), automated extraction, business glossaries, data discovery, impact analysis, lineage tracking, and building a metadata system. Include architecture."),

    # ============================================
    # AI & ML ADVANCED (20)
    # ============================================
    ("transformer_deep_dive", "Transformer self-attention multi-head positional encoding", "Write an expert guide to the Transformer architecture: self-attention math, multi-head attention, positional encoding, layer normalization, feed-forward networks, encoder-decoder, and building a Transformer from scratch in PyTorch. Include complete code."),
    ("llm_training", "LLM training data collection tokenizer BPE distributed DeepSpeed", "Write an expert guide to training LLMs: data collection/cleaning, tokenizer training (BPE, SentencePiece), pre-training objectives, distributed training (DeepSpeed, FSDP), mixed precision, learning rate scheduling, and the complete pipeline. Include code."),
    ("llm_finetuning", "LLM fine-tuning LoRA QLoRA RLHF DPO instruction tuning", "Write an expert guide to LLM fine-tuning: full fine-tuning, LoRA, QLoRA, adapter methods, prefix tuning, prompt tuning, RLHF, DPO, instruction tuning datasets, evaluation, and deploying fine-tuned models. Include code."),
    ("rag_advanced", "RAG chunking reranking HyDE hybrid search contextual compression", "Write an expert guide to advanced RAG: chunking strategies, embedding selection, hybrid search (dense+sparse), reranking, query expansion, HyDE, contextual compression, multi-step RAG, and evaluating RAG quality. Include code."),
    ("vector_databases_deep", "vector database HNSW IVF product quantization ChromaDB Pinecone", "Write an expert guide to vector databases: HNSW algorithm, IVF indexes, product quantization, distance metrics, ChromaDB internals, Pinecone, Weaviate, Milvus, Qdrant, embedding optimization, and choosing the right one. Include benchmarks."),
    ("computer_vision_advanced", "computer vision YOLO DETR SAM segmentation pose depth", "Write an expert guide to advanced computer vision: object detection (YOLO v8, DETR), segmentation (Mask R-CNN, SAM), pose estimation, depth estimation, optical flow, 3D reconstruction, video understanding, and edge deployment. Include PyTorch code."),
    ("reinforcement_learning_deep", "reinforcement learning DQN PPO SAC multi-agent sim-to-real", "Write an expert guide to advanced RL: DQN, policy gradients (REINFORCE, A2C, A3C), PPO, SAC, model-based RL, multi-agent RL, reward shaping, curriculum learning, sim-to-real, and building an RL agent. Include code."),
    ("generative_ai_deep", "diffusion models Stable Diffusion ControlNet LoRA inpainting", "Write an expert guide to generative AI: diffusion model math, U-Net, classifier-free guidance, DDPM vs DDIM, ControlNet, IP-Adapter, LoRA for images, Stable Diffusion pipeline, inpainting, and fine-tuning. Include code."),
    ("speech_audio_ai", "speech recognition Whisper TTS voice cloning diarization", "Write an expert guide to speech and audio AI: speech recognition (Whisper), speaker diarization, voice activity detection, TTS (Bark, XTTS), voice cloning, audio classification, music generation, and building a voice assistant. Include code."),
    ("ml_from_scratch", "implement ML algorithms from scratch linear regression decision tree SVM", "Write an expert guide to implementing ML from scratch: linear regression, logistic regression, decision trees, random forests, k-means, KNN, naive Bayes, SVM, and neural networks. For each: math, Python code without libraries, and comparison with scikit-learn."),
    ("graph_neural_networks", "graph neural networks GCN GraphSAGE GAT PyTorch Geometric", "Write an expert guide to graph neural networks: graph representation, message passing, GCN, GraphSAGE, GAT, graph transformers, link prediction, node classification, and implementing with PyTorch Geometric. Include code."),
    ("federated_learning", "federated learning FedAvg differential privacy Flower", "Write an expert guide to federated learning: architecture, FedAvg, communication efficiency, privacy guarantees, differential privacy, secure aggregation, heterogeneous data, and implementing with Flower. Include code."),
    ("causal_inference", "causal inference propensity matching instrumental variables DoWhy", "Write an expert guide to causal inference: correlation vs causation, experiments, propensity score matching, instrumental variables, difference-in-differences, regression discontinuity, causal forests, and DoWhy library. Include code."),
    ("ai_interpretability", "AI interpretability SHAP LIME attention saliency counterfactual", "Write an expert guide to AI interpretability: feature importance, SHAP, LIME, attention visualization, saliency maps, concept activation vectors, counterfactual explanations, model cards, and building interpretable systems. Include code."),
    ("anomaly_detection", "anomaly detection isolation forest autoencoder time series fraud", "Write an expert guide to anomaly detection: statistical methods, isolation forest, autoencoders, time series anomalies, network anomalies, fraud detection, and building a real-time anomaly pipeline. Include code."),
    ("recommendation_advanced", "recommendation systems collaborative filtering two-tower embeddings", "Write an expert guide to advanced recommendations: collaborative filtering at scale, content-based with embeddings, two-tower models, sequential recommendations, contextual bandits, diversity, cold start, and building production recommenders. Include code."),
    ("time_series_forecasting", "time series forecasting ARIMA Prophet LSTM Transformer", "Write an expert guide to time series forecasting: ARIMA, SARIMA, exponential smoothing, Prophet, LSTM, Transformer models, feature engineering, evaluation metrics, and handling seasonality. Include Python code."),
    ("ml_deployment", "ML deployment ONNX TorchServe Triton BentoML A/B shadow", "Write an expert guide to ML deployment: model serialization (ONNX, TorchScript), serving (TorchServe, Triton, BentoML), containers, A/B testing, shadow deployment, monitoring, feature stores, and building an ML platform. Include code."),
    ("ai_safety_alignment", "AI safety alignment RLHF constitutional AI red teaming guardrails", "Write an expert guide to AI safety: output filtering, content moderation, jailbreak prevention, instruction hierarchy, RLHF, constitutional AI, red teaming, capability boundaries, and building safety guardrails. Include implementation code."),
    ("ai_local_optimization", "local AI inference quantization GGUF KV cache speculative decoding", "Write an expert guide to optimizing local AI: quantization (GPTQ, AWQ, GGUF), KV cache optimization, speculative decoding, batching, memory mapping, CPU optimization (SIMD), and getting maximum performance from consumer hardware. Include benchmarks."),

    # ============================================
    # SECURITY DEEP (10)
    # ============================================
    ("offensive_security", "offensive security reconnaissance exploitation privilege escalation", "Write an expert guide to offensive security for defenders: reconnaissance, vulnerability scanning, exploitation, privilege escalation, lateral movement, persistence, and how understanding attackers improves defense. Include detection strategies."),
    ("zero_trust", "zero trust architecture micro-segmentation BeyondCorp device trust", "Write an expert guide to zero trust: never trust always verify, identity-based access, micro-segmentation, device trust, continuous verification, BeyondCorp, and implementing step by step. Include architecture."),
    ("supply_chain_security", "software supply chain SBOM Sigstore SLSA reproducible builds", "Write an expert guide to supply chain security: dependency scanning, SBOM, Sigstore, SLSA, reproducible builds, artifact signing, and protecting against dependency confusion. Include examples."),
    ("threat_modeling", "threat modeling STRIDE PASTA attack trees data flow trust", "Write an expert guide to threat modeling: STRIDE, PASTA, attack trees, data flow diagrams, trust boundaries, risk scoring, and running threat modeling sessions. Include practical examples."),
    ("secrets_management", "secrets management Vault AWS Secrets Manager sealed secrets SOPS", "Write an expert guide to secrets management: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, sealed secrets for Kubernetes, SOPS, age encryption, rotation, and building a secrets strategy. Include code."),
    ("compliance_frameworks", "compliance SOC 2 ISO 27001 GDPR HIPAA PCI DSS FedRAMP", "Write an expert guide to compliance: SOC 2 (Type I/II), ISO 27001, GDPR technical requirements, HIPAA, PCI DSS, FedRAMP, and implementing controls in cloud environments. Include checklists."),
    ("security_monitoring", "SIEM detection engineering SIGMA MITRE ATT&CK threat intelligence", "Write an expert guide to security monitoring: SIEM (Splunk, Elastic), detection engineering, SIGMA rules, MITRE ATT&CK, alert tuning, threat intelligence, and building a SOC. Include detection rules."),
    ("cryptography_applied", "applied cryptography E2E encryption Signal TLS cert-manager", "Write an expert guide to applied cryptography: end-to-end encryption, Signal protocol, age encryption, TLS certificate management (Let's Encrypt, cert-manager), key management, and building encrypted systems. Include code."),
    ("api_security_deep", "API security OAuth2 rate limiting token bucket GraphQL gRPC abuse", "Write an expert guide to API security: authentication methods, API key management, OAuth2 security, rate limiting algorithms (token bucket, leaky bucket), input validation, GraphQL security, gRPC security, and abuse prevention. Include code."),
    ("incident_response", "incident response IR detection containment forensics threat hunting", "Write an expert guide to incident response: IR planning, detection and analysis, containment, eradication, recovery, post-incident review, forensics, log analysis, threat hunting, and building an IR team."),

    # ============================================
    # BUSINESS & STRATEGY (16)
    # ============================================
    ("startup_playbook", "startup playbook validation MVP pivot co-founder first customers", "Write an expert guide as a startup playbook: idea validation (20 methods), MVP types, customer discovery, pivot framework, co-founder selection, advisor relationships, culture, first 10 customers, first 10 employees, and year one timeline."),
    ("product_led_growth", "PLG product-led growth freemium activation self-serve expansion", "Write an expert guide to product-led growth: PLG flywheel, free-to-paid conversion, product-qualified leads, self-serve onboarding, activation metrics, expansion revenue, usage-based pricing, and case studies (Slack, Dropbox, Figma)."),
    ("enterprise_sales", "enterprise sales complex multi-stakeholder procurement champion", "Write an expert guide to enterprise sales: complex cycles, multi-stakeholder selling, champion building, procurement, security reviews, RFP response, POC management, contract negotiation, and building an enterprise sales machine."),
    ("marketplace_business", "marketplace chicken-egg supply demand liquidity network effects", "Write an expert guide to marketplaces: chicken-and-egg problem, supply acquisition, demand generation, matching, trust and safety, pricing (take rates), liquidity, metrics, network effects, and scaling strategies."),
    ("platform_strategy", "platform strategy API-first two-sided networks developer ecosystem moats", "Write an expert guide to platform strategy: platform vs product, two-sided networks, API-first business, developer ecosystems, governance, pricing, defense (moats), and case studies (AWS, Shopify, Stripe, Twilio)."),
    ("m_and_a_tech", "M&A acquisition due diligence integration talent retention", "Write an expert guide to tech M&A: acquisition strategy, target identification, valuation, due diligence (technical, financial, legal), integration planning, talent retention, and post-merger optimization."),
    ("venture_capital", "venture capital fund economics GP LP carry portfolio due diligence", "Write an expert guide to venture capital from both sides: VC evaluation, due diligence, portfolio construction, fund economics (GP/LP, carry, fees), board dynamics, and exit strategies."),
    ("financial_markets", "financial markets stocks options derivatives algorithmic trading CAPM", "Write an expert guide to financial markets: stocks, bonds, derivatives (options, futures), forex, algorithmic trading, portfolio theory (CAPM), risk management (VaR), and quantitative finance. Include Python code."),
    ("crypto_defi_finance", "tokenomics yield farming liquidity pools impermanent loss DAO treasury", "Write an expert guide to crypto/DeFi finance: tokenomics, yield farming, liquidity pool math, impermanent loss, lending protocols, stablecoins, governance tokens, DAO treasury, and DeFi risk."),
    ("startup_operations", "startup operations LLC C-Corp equity vesting stock options tax", "Write an expert guide to startup operations: formation (LLC, C-Corp, Delaware), equity structure, vesting, stock options, employment law, contractors, insurance, accounting, and tax strategy."),
    ("customer_development", "customer development problem interviews MVP testing NPS cohort", "Write an expert guide to customer development: problem interviews, solution interviews, MVP testing, landing page experiments, concierge MVP, feedback loops, NPS, CSAT, cohort analysis, and advisory boards. Include scripts."),
    ("strategic_planning", "strategic planning competitive analysis OKR Porter SWOT scenario", "Write an expert guide to strategic planning: vision/mission, competitive analysis (Porter's Five Forces), SWOT, Blue Ocean, OKRs, balanced scorecard, scenario planning, pivots, and annual planning. Include templates."),
    ("team_scaling", "scaling engineering teams hiring pipeline onboarding career ladders", "Write an expert guide to scaling teams: hiring pipeline, interviews, onboarding, engineering levels, career ladders, performance reviews, compensation, diversity, managing managers, and organizational design."),
    ("board_management", "board management board meetings deck investor expectations governance", "Write an expert guide to board management: composition, meeting prep, board decks, investor expectations, committee structure, between-meeting communication, difficult conversations, and governance. Include templates."),
    ("exit_strategy", "exit strategy IPO direct listing SPAC acquisition PE buyout", "Write an expert guide to exit strategies: IPO preparation, direct listing, SPAC, strategic acquisition, PE buyout, management buyout, secondary sales, timing, valuation multiples, and the exit process."),
    ("revenue_operations", "RevOps revenue operations sales marketing alignment forecasting", "Write an expert guide to revenue operations: aligning sales/marketing/success, forecasting, pipeline management, lead scoring, attribution, customer lifecycle, revenue tech stack, and building RevOps."),

    # ============================================
    # SCIENCE & ENGINEERING (12)
    # ============================================
    ("physics_computing", "physics computing simulation electromagnetism thermodynamics quantum", "Write an expert guide to physics for computing: classical mechanics simulation, electromagnetism, thermodynamics (cooling), optics (displays), semiconductor physics, quantum mechanics basics, and physics in engineering. Include Python simulations."),
    ("electrical_engineering", "electrical engineering circuits microcontrollers Arduino ESP32 I2C SPI", "Write an expert guide to EE for software engineers: circuits, digital logic, microcontrollers (Arduino, ESP32), sensors, PCB basics, signal processing, serial protocols (I2C, SPI, UART), and embedded systems. Include code."),
    ("biotechnology", "biotechnology CRISPR PCR DNA sequencing synthetic biology bioinformatics", "Write an expert guide to biotechnology: CRISPR, PCR, DNA sequencing, protein engineering, synthetic biology, bioinformatics pipelines, lab automation, biotech startups, and AI in biotech. Include Python code."),
    ("climate_science", "climate science greenhouse carbon capture renewable energy smart grid", "Write an expert guide to climate and technology: greenhouse effect, climate models, carbon capture, renewables (solar, wind, nuclear), energy storage, smart grids, carbon accounting, and climate tech solutions."),
    ("space_technology", "space technology orbital mechanics satellites CubeSats Earth observation", "Write an expert guide to space technology: orbital mechanics, satellite design, communications, ground stations, Earth observation, satellite internet (Starlink), CubeSats, and software for space. Include Python calculations."),
    ("neuroscience_ai", "neuroscience AI biological neural networks brain-computer interfaces neuromorphic", "Write an expert guide to neuroscience for AI: biological networks, learning and memory, attention in the brain, RL in biology, brain-computer interfaces, neuromorphic computing, and how neuroscience inspires AI."),
    ("autonomous_vehicles", "autonomous vehicles sensor fusion LIDAR perception CARLA V2X SAE", "Write an expert guide to autonomous vehicles: sensor fusion, perception, localization, path planning, decision making, control, simulation (CARLA), HD maps, V2X, safety validation, and SAE levels."),
    ("iot_systems", "IoT MQTT LoRaWAN digital twins edge OTA security", "Write an expert guide to IoT systems: sensor networks, MQTT, LoRaWAN, IoT platforms, edge processing, digital twins, OTA updates, IoT security, data pipelines, and building a complete IoT system. Include code."),
    ("robotics_advanced", "robotics kinematics motion planning manipulation visual servoing swarm", "Write an expert guide to advanced robotics: kinematics, dynamics, motion planning, manipulation, grasping, visual servoing, human-robot interaction, swarm robotics, soft robotics, and industrial robots. Include code."),
    ("biomedical_engineering", "biomedical health tech medical device FHIR HL7 FDA wearables", "Write an expert guide to health tech: medical device software (IEC 62304), health data (HL7, FHIR), wearable sensors, telemedicine, FDA regulation, clinical trials data, and building health tech apps. Include examples."),
    ("quantum_computing", "quantum computing qubits superposition entanglement Qiskit Shor Grover", "Write an expert guide to quantum computing: qubits, superposition, entanglement, quantum gates, circuits, Shor's algorithm, Grover's algorithm, error correction, hardware, and Qiskit programming. Include code."),
    ("materials_science", "materials science semiconductors OLED batteries graphene carbon nanotubes", "Write an expert guide to materials science for tech: semiconductors, display tech (LCD, OLED, MicroLED), battery chemistry, fiber optics, magnetic storage, thermal management, and future materials (graphene)."),

    # ============================================
    # CREATIVE & HUMANITIES (10)
    # ============================================
    ("3d_graphics", "3D graphics transformations projection shaders PBR rendering pipeline", "Write an expert guide to 3D graphics: coordinate systems, transformations, projection, lighting (Phong, PBR), textures, shaders (vertex, fragment), scene graphs, and building a simple renderer. Include code."),
    ("audio_programming", "audio programming FFT synthesis MIDI real-time effects reverb", "Write an expert guide to audio programming: digital audio fundamentals, formats, real-time processing, FFT, synthesis (additive, subtractive, FM), effects (reverb, delay), MIDI, and building an audio app. Include code."),
    ("data_visualization", "data visualization D3.js Tufte dashboard storytelling accessible", "Write an expert guide to data visualization: Tufte's principles, chart selection, color theory, interactive viz (D3.js), dashboards, data storytelling, accessibility, and building publication-quality charts. Include code."),
    ("game_design_theory", "game design player motivation flow mechanics economy narrative procedural", "Write an expert guide to game design: player motivation (Bartle), flow state, mechanics, economy design, narrative design, procedural generation, difficulty balancing, multiplayer, monetization ethics, and analysis."),
    ("music_technology", "music technology DAW MIDI synthesis sampling mixing VST synthesizer", "Write an expert guide to music technology: DAWs, MIDI, synthesis (additive, subtractive, FM, granular, wavetable), sampling, mixing, mastering, VST development, and building a synthesizer. Include code."),
    ("philosophy_technology", "philosophy technology ethics algorithms surveillance attention digital rights", "Write an expert guide to philosophy of technology: determinism, social construction, ethics of algorithms, surveillance capitalism, digital rights, attention economy, addiction, and building humane technology."),
    ("history_computing", "history computing Babbage Turing transistor mainframe internet AI", "Write an expert guide to computing history: Babbage and Lovelace, Turing and Von Neumann, transistors, mainframes, personal computers, internet, mobile revolution, cloud, AI winters and springs, and lessons."),
    ("psychology_product", "psychology product design cognitive biases habit Hook model dark patterns", "Write an expert guide to psychology for product design: cognitive biases in UX, habit formation (Hook model), motivation (SDT), social proof, anchoring, loss aversion, choice architecture, dark patterns, and ethical persuasion."),
    ("education_technology", "edtech learning management adaptive spaced repetition AI tutoring", "Write an expert guide to education technology: LMS, adaptive learning, spaced repetition, gamification, assessment design, accessibility, AI tutoring, and building effective educational software. Include examples."),
    ("journalism_data", "data journalism investigative OSINT scraping fact-checking visualization", "Write an expert guide to data journalism: investigative analysis, web scraping for journalism, OSINT, data visualization for news, fact-checking tools, and building journalism tools. Include Python code."),

    # ============================================
    # PERSONAL DEVELOPMENT (10)
    # ============================================
    ("decision_making", "decision making expected value pre-mortem reversible Bayesian updating", "Write an expert guide to decision making: expected value, Bayesian updating, pre-mortem analysis, decision journals, second-order thinking, reversible vs irreversible, group methods (Delphi), and building a decision framework."),
    ("creativity_innovation", "creativity innovation brainstorming SCAMPER design sprints blue ocean", "Write an expert guide to creativity: divergent thinking, brainstorming (SCAMPER, Six Thinking Hats, mind mapping), design sprints, innovation frameworks, prototyping mindset, and building innovation culture."),
    ("emotional_intelligence", "emotional intelligence self-awareness empathy difficult conversations feedback", "Write an expert guide to emotional intelligence for tech: self-awareness, self-regulation, motivation, empathy, social skills, stress management, difficult conversations, feedback, trust, and leading with EQ."),
    ("financial_independence", "FIRE financial independence savings rate portfolio withdrawal 4% rule", "Write an expert guide to financial independence: FIRE movement, savings rate, investment portfolios, real estate, side businesses, tax optimization, withdrawal strategies (4% rule), and building wealth in tech. Include calculations."),
    ("health_optimization", "health optimization ergonomics exercise sleep nutrition stress RSI", "Write an expert guide to health for knowledge workers: ergonomics, exercise for brain performance, sleep optimization, nutrition, stress management, eye health, preventing RSI, and sustainable health habits."),
    ("teaching_mentoring", "teaching mentoring adult learning scaffolding Bloom pair programming", "Write an expert guide to teaching and mentoring: adult learning theory, scaffolding, Bloom's taxonomy, tutorials, code review as teaching, pair programming, workshops, online courses, and developing careers."),
    ("open_source", "open source license community documentation governance funding sustainability", "Write an expert guide to open source: choosing a license, building community, documentation, issue management, PR workflows, code of conduct, governance, funding (sponsors, grants), marketing, and sustainability."),
    ("developer_productivity", "developer productivity IDE Git dotfiles terminal automation snippets", "Write an expert guide to developer productivity: IDE mastery (VS Code), Git workflows, dotfiles, terminal customization, shell scripting, automation, code snippets, documentation-driven development, and time tracking."),
    ("personal_brand", "personal brand tech blogging Twitter LinkedIn YouTube newsletter", "Write an expert guide to personal brand in tech: blogging, Twitter/X strategy, LinkedIn, YouTube, podcast guesting, conference speaking, newsletter building, GitHub profile, and monetization."),
    ("writing_mastery", "writing mastery voice editing daily practice long-form newsletter books", "Write an expert guide to writing mastery: finding your voice, writer's block, editing techniques, daily practice, long-form writing, books, newsletters, platform writing, and building a writing career."),

    # ============================================
    # AUTONOMOUS AI BUILDING BLOCKS (16)
    # ============================================
    ("autonomous_reasoning", "autonomous AI reasoning chain-of-thought tree-of-thought reflexion self-correction", "Write an expert guide to autonomous reasoning: chain-of-thought, tree-of-thought, self-consistency, reflexion, step-by-step verification, problem decomposition, planning algorithms, goal-oriented behavior, and building a reasoning engine. Include code."),
    ("autonomous_code_gen", "autonomous code generation AST code repair test generation refactoring", "Write an expert guide to autonomous code generation: natural language to code, AST manipulation, code repair, test generation, refactoring automation, code review automation, and building a system that writes and tests code. Include code."),
    ("autonomous_research", "autonomous research agent web search source evaluation synthesis report", "Write an expert guide to autonomous research: web search strategies, source evaluation, information extraction, fact verification, synthesis, report generation, and building a system that researches any topic. Include code."),
    ("autonomous_planning", "autonomous AI planning STRIPS hierarchical MCTS goal decomposition", "Write an expert guide to AI planning: STRIPS, hierarchical task networks, PDDL, Monte Carlo tree search, backward/forward chaining, partial-order planning, and building an autonomous planner. Include code."),
    ("self_improving_ai", "self-improving AI performance monitoring weakness identification prompt optimization", "Write an expert guide to self-improving AI: monitoring, identifying weaknesses, generating training data, fine-tuning loops, A/B testing models, knowledge curation automation, prompt optimization, and continuous improvement. Include architecture."),
    ("ai_tool_creation", "AI tool creation dynamic function generation API discovery sandbox testing", "Write an expert guide to AI systems that create tools: dynamic function generation, API discovery, tool composition, sandbox testing, tool versioning, and building an AI that creates its own capabilities. Include code."),
    ("ai_memory_advanced", "AI memory retrieval importance scoring compression hierarchical consolidation", "Write an expert guide to advanced AI memory: episodic optimization, semantic consolidation, retrieval algorithms, importance scoring, compression, hierarchical memory, forgetting curves, and intelligent memory management. Include code."),
    ("ai_self_monitoring", "AI self-monitoring confidence calibration hallucination detection quality scoring", "Write an expert guide to AI self-monitoring: confidence calibration, hallucination detection, quality scoring, consistency checking, factual grounding, and building a system that evaluates its own outputs. Include code."),
    ("ai_conversation", "AI conversation context management personality multi-turn reasoning coherence", "Write an expert guide to conversational AI: context management, personality consistency, emotional intelligence, multi-turn reasoning, handling ambiguity, clarifying questions, and building a natural conversation engine. Include code."),
    ("ai_knowledge_synthesis", "AI knowledge synthesis combining sources contradiction resolution gap identification", "Write an expert guide to knowledge synthesis: combining sources, resolving contradictions, identifying gaps, multi-level summaries, structured knowledge from unstructured text, and building a synthesis system. Include code."),
    ("build_search_engine", "build search engine inverted index TF-IDF crawler ranking snippets", "Write a complete guide to building a search engine: inverted index, TF-IDF scoring, web crawler, query parsing, ranking, snippet generation, and web interface. Include all Python code and commands."),
    ("build_database_full", "build database B-tree WAL SQL parser query executor transactions", "Write a complete guide to building a database: B-tree, write-ahead log, buffer pool, SQL parser, query executor, transactions (MVCC), and client interface. Include all Python code and commands."),
    ("build_web_framework", "build web framework HTTP routing middleware template static sessions", "Write a complete guide to building a web framework: HTTP parser, routing, middleware, template engine, static files, request/response objects, and sessions. Include all Python code and commands."),
    ("build_message_queue", "build message queue topics producers consumers persistence exactly-once", "Write a complete guide to building a message queue: topic management, producer/consumer, persistence, consumer groups, exactly-once delivery, dead letters, and admin API. Include all code and commands."),
    ("build_blockchain_full", "build complete blockchain proof of work wallet P2P mining REST API", "Write a complete guide to building a blockchain: blocks, SHA-256, chain validation, proof-of-work, transaction pool, wallet (keys), P2P networking, mining, and REST API. Include all Python code and commands."),
    ("build_compiler_full", "build compiler lexer parser AST type checker code generator REPL", "Write a complete guide to building a compiler: lexer, parser (recursive descent), AST, type checker, code generator, and REPL. Include all Python code and commands."),
]

print("=" * 60)
print("  ACUMEN MAXIMUM KNOWLEDGE PACK")
print("  Smart Download - Skips Known Topics")
print("=" * 60)

memory = MemoryManager()
before = memory.knowledge_count()
print(f"  Current knowledge base: {before} docs")

skip_count = 0
download_list = []
for topic_id, search_term, prompt in topics:
    if topic_exists(memory, search_term):
        skip_count += 1
    else:
        download_list.append((topic_id, prompt))

print(f"  Topics already known: {skip_count} (skipping)")
print(f"  New topics to learn: {len(download_list)}")
print()

if len(download_list) == 0:
    print("  Nothing new to download! Knowledge base is comprehensive.")
else:
    total_chunks = 0
    errors = 0
    start_time = time.time()

    for i, (topic_id, prompt) in enumerate(download_list):
        print(f"[{i+1}/{len(download_list)}] {topic_id}...", end=" ", flush=True)
        try:
            content = ask_claude(topic_id, prompt)
            chunks = ingest_text(content, topic=topic_id, source="claude_maximum")
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
    print("  MAXIMUM KNOWLEDGE PACK COMPLETE!")
    print("=" * 60)
    print(f"  Knowledge base: {before} -> {after} docs")
    print(f"  New chunks: {total_chunks}")
    print(f"  Skipped (already known): {skip_count}")
    print(f"  Errors: {errors}")
    print(f"  Time: {elapsed:.1f} minutes")
    print("=" * 60)