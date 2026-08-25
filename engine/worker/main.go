package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os/exec"
	"sync"
	"time"
)

// TaskRequest from the scheduler
type TaskRequest struct {
	ID      string `json:"id"`
	Name    string `json:"name"`
	Agent   string `json:"agent"`
	Payload string `json:"payload"`
	Timeout int    `json:"timeout_seconds"`
}

// TaskResult back to the scheduler
type TaskResult struct {
	TaskID   string  `json:"task_id"`
	Status   string  `json:"status"`
	Output   string  `json:"output"`
	Duration float64 `json:"duration_seconds"`
}

// WorkerPool manages concurrent task execution
type WorkerPool struct {
	maxWorkers int
	semaphore  chan struct{}
	mu         sync.Mutex
	results    map[string]TaskResult
}

func NewWorkerPool(size int) *WorkerPool {
	return &WorkerPool{
		maxWorkers: size,
		semaphore:  make(chan struct{}, size),
		results:    make(map[string]TaskResult),
	}
}

// Execute runs a task by calling the Python agent layer
func (wp *WorkerPool) Execute(task TaskRequest) {
	wp.semaphore <- struct{}{} // Acquire slot
	go func() {
		defer func() { <-wp.semaphore }() // Release slot
		start := time.Now()

		cmd := exec.Command("python", "-c", fmt.Sprintf(
			"from acumen.agents.crews import *; "+
				"print(%s_crew('%s').kickoff())",
			task.Agent, task.Payload))

		output, err := cmd.CombinedOutput()
		duration := time.Since(start).Seconds()

		result := TaskResult{
			TaskID:   task.ID,
			Duration: duration,
		}

		if err != nil {
			result.Status = "failed"
			result.Output = string(output)
		} else {
			result.Status = "completed"
			result.Output = string(output)
		}

		wp.mu.Lock()
		wp.results[task.ID] = result
		wp.mu.Unlock()
	}()
}

func corsHandler(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			w.WriteHeader(200)
			return
		}
		next(w, r)
	}
}

func main() {
	pool := NewWorkerPool(4)

	http.HandleFunc("/execute", corsHandler(func(w http.ResponseWriter, r *http.Request) {
		var task TaskRequest
		json.NewDecoder(r.Body).Decode(&task)
		pool.Execute(task)
		json.NewEncoder(w).Encode(map[string]string{
			"status": "accepted", "task_id": task.ID})
	}))

	http.HandleFunc("/result", corsHandler(func(w http.ResponseWriter, r *http.Request) {
		taskID := r.URL.Query().Get("id")
		pool.mu.Lock()
		result, ok := pool.results[taskID]
		pool.mu.Unlock()
		if !ok {
			json.NewEncoder(w).Encode(map[string]string{"status": "pending"})
			return
		}
		json.NewEncoder(w).Encode(result)
	}))

	fmt.Println("Acumen Worker Pool starting on :9091...")
	http.ListenAndServe(":9091", nil)
}