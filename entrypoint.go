package main

import (
	"log"
	"os"
	"os/exec"
)

func generateVersionStatusFile() {
	cmd := exec.Command("/usr/local/bin/python3", "-m", "app.services.scheduler.version_check")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		log.Printf("[entrypoint] ⚠️ Failed to write version_status.json: %v", err)
	} else {
		log.Println("[entrypoint] ✅ version_status.json written successfully")
	}
}

func main() {
	// ✅ Run this first
	generateVersionStatusFile()

	// Then start Gunicorn
	port := os.Getenv("FLASK_APP_PORT")
	if port == "" {
		port = "5069"
	}
	args := []string{
		"-c", "gunicorn.conf.py",
		"-b", "0.0.0.0:" + port,
		"wsgi:app",
	}
	cmd := exec.Command("/usr/local/bin/gunicorn", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = os.Environ()
	cmd.Run()
}
