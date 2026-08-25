use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use tower_http::cors::{CorsLayer, Any};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::Arc;
use tokio::sync::Mutex;

// ── Data Structures ──

#[derive(Debug, Clone, Deserialize, Serialize)]
struct DagTask {
    id: String,
    name: String,
    agent: String,
    payload: String,
    depends_on: Vec<String>,
    priority: i32,
}

#[derive(Debug, Clone, Serialize)]
struct ScheduleResult {
    pipeline_id: String,
    execution_order: Vec<String>,
    ready_tasks: Vec<DagTask>,
    status: String,
}

#[derive(Debug, Clone, Serialize)]
struct PipelineStatus {
    total_tasks: usize,
    completed: Vec<String>,
    failed: Vec<String>,
    ready: Vec<String>,
    is_complete: bool,
}

#[derive(Deserialize)]
struct ScheduleRequest {
    tasks: Vec<DagTask>,
}

#[derive(Deserialize)]
struct MarkRequest {
    task_id: String,
    status: String,
}

// ── DAG Scheduler Logic ──

struct DagScheduler {
    tasks: HashMap<String, DagTask>,
    completed: HashSet<String>,
    failed: HashSet<String>,
}

impl DagScheduler {
    fn new() -> Self {
        DagScheduler {
            tasks: HashMap::new(),
            completed: HashSet::new(),
            failed: HashSet::new(),
        }
    }

    fn load_tasks(&mut self, tasks: Vec<DagTask>) {
        self.tasks.clear();
        self.completed.clear();
        self.failed.clear();
        for t in tasks {
            self.tasks.insert(t.id.clone(), t);
        }
    }

    fn validate(&self) -> Result<Vec<String>, String> {
        let mut in_degree: HashMap<&str, usize> = HashMap::new();
        let mut adj: HashMap<&str, Vec<&str>> = HashMap::new();

        for (id, task) in &self.tasks {
            in_degree.entry(id.as_str()).or_insert(0);
            for dep in &task.depends_on {
                adj.entry(dep.as_str()).or_default().push(id.as_str());
                *in_degree.entry(id.as_str()).or_insert(0) += 1;
            }
        }

        let mut queue: VecDeque<&str> = in_degree
            .iter()
            .filter(|(_, &d)| d == 0)
            .map(|(&id, _)| id)
            .collect();

        let mut order = Vec::new();
        while let Some(node) = queue.pop_front() {
            order.push(node.to_string());
            if let Some(neighbors) = adj.get(node) {
                for &next in neighbors {
                    let d = in_degree.get_mut(next).unwrap();
                    *d -= 1;
                    if *d == 0 {
                        queue.push_back(next);
                    }
                }
            }
        }

        if order.len() == self.tasks.len() {
            Ok(order)
        } else {
            Err("Cycle detected in DAG!".to_string())
        }
    }

    fn get_ready_tasks(&self) -> Vec<DagTask> {
        let mut ready: Vec<DagTask> = self
            .tasks
            .values()
            .filter(|t| {
                !self.completed.contains(&t.id)
                    && !self.failed.contains(&t.id)
                    && t.depends_on.iter().all(|dep| self.completed.contains(dep))
            })
            .cloned()
            .collect();
        ready.sort_by(|a, b| b.priority.cmp(&a.priority));
        ready
    }

    fn mark_completed(&mut self, task_id: &str) {
        self.completed.insert(task_id.to_string());
    }

    fn mark_failed(&mut self, task_id: &str) {
        self.failed.insert(task_id.to_string());
    }

    fn is_complete(&self) -> bool {
        self.completed.len() + self.failed.len() == self.tasks.len()
    }

    fn get_status(&self) -> PipelineStatus {
        PipelineStatus {
            total_tasks: self.tasks.len(),
            completed: self.completed.iter().cloned().collect(),
            failed: self.failed.iter().cloned().collect(),
            ready: self
                .get_ready_tasks()
                .iter()
                .map(|t| t.id.clone())
                .collect(),
            is_complete: self.is_complete(),
        }
    }
}

// ── Shared State ──

type AppState = Arc<Mutex<DagScheduler>>;

// ── HTTP Handlers ──

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "healthy",
        "service": "acumen-dag-scheduler",
        "port": 9090
    }))
}

async fn schedule(
    State(state): State<AppState>,
    Json(req): Json<ScheduleRequest>,
) -> Result<Json<ScheduleResult>, (StatusCode, String)> {
    let mut scheduler: tokio::sync::MutexGuard<'_, DagScheduler> = state.lock().await;
    scheduler.load_tasks(req.tasks);

    match scheduler.validate() {
        Ok(order) => {
            let ready = scheduler.get_ready_tasks();
            let pid = format!("pipe_{}", chrono::Utc::now().timestamp());
            println!(
                "[SCHEDULER] Pipeline {} loaded: {} tasks, order: {:?}",
                pid,
                order.len(),
                order
            );
            Ok(Json(ScheduleResult {
                pipeline_id: pid,
                execution_order: order,
                ready_tasks: ready,
                status: "scheduled".to_string(),
            }))
        }
        Err(e) => {
            println!("[SCHEDULER] ERROR: {}", e);
            Err((StatusCode::BAD_REQUEST, e))
        }
    }
}

async fn get_status(State(state): State<AppState>) -> Json<PipelineStatus> {
    let scheduler: tokio::sync::MutexGuard<'_, DagScheduler> = state.lock().await;
    Json(scheduler.get_status())
}

async fn mark_task(
    State(state): State<AppState>,
    Json(req): Json<MarkRequest>,
) -> Json<serde_json::Value> {
    let mut scheduler: tokio::sync::MutexGuard<'_, DagScheduler> = state.lock().await;
    match req.status.as_str() {
        "completed" => {
            scheduler.mark_completed(&req.task_id);
            println!("[SCHEDULER] Task {} completed", req.task_id);
        }
        "failed" => {
            scheduler.mark_failed(&req.task_id);
            println!("[SCHEDULER] Task {} failed", req.task_id);
        }
        _ => {}
    }
    let ready = scheduler.get_ready_tasks();
    Json(serde_json::json!({
        "next_ready": ready.iter().map(|t| &t.id).collect::<Vec<_>>(),
        "is_complete": scheduler.is_complete()
    }))
}

// ── Main ──

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let state: AppState = Arc::new(Mutex::new(DagScheduler::new()));

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let app = Router::new()
        .route("/health", get(health))
        .route("/schedule", post(schedule))
        .route("/status", get(get_status))
        .route("/mark", post(mark_task))
        .layer(cors)
        .with_state(state);

    println!("Acumen DAG Scheduler running on http://127.0.0.1:9090");
    let listener = tokio::net::TcpListener::bind("127.0.0.1:9090")
        .await
        .expect("Failed to bind port 9090");
    axum::serve(listener, app).await.unwrap();
}