package main

import (
	"os"
	"os/exec"
)

func main() {
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
