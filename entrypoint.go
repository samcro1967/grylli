// ---------------------------------------------------------------------
// entrypoint.go
// Project root
// Verifies file integrity, then starts the app via Gunicorn
// ---------------------------------------------------------------------

package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
)

var (
	hashFile = "file_hashes.sha256"

	optionalFiles = map[string]bool{
		"scripts/generate_screenshots.py": true,
		"scripts/init_db.py":              true,
	}
)

func computeHash(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	h := sha256.New()
	buf := make([]byte, 8192)
	for {
		n, err := f.Read(buf)
		if n > 0 {
			h.Write(buf[:n])
		}
		if err != nil {
			break
		}
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func checkIntegrity() error {
	file, err := os.Open(hashFile)
	if err != nil {
		return fmt.Errorf("missing hash file: %v", err)
	}
	defer file.Close()

	var failures []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.TrimSpace(line) == "" {
			continue
		}
		parts := strings.SplitN(line, " ", 2)
		if len(parts) != 2 {
			failures = append(failures, fmt.Sprintf("invalid line: %s", line))
			continue
		}
		expected := parts[0]
		relPath := strings.TrimSpace(parts[1])

		if _, err := os.Stat(relPath); os.IsNotExist(err) {
			if optionalFiles[relPath] {
				continue
			}
			failures = append(failures, fmt.Sprintf("Missing file: %s", relPath))
			continue
		}

		actual, err := computeHash(relPath)
		if err != nil {
			failures = append(failures, fmt.Sprintf("Failed to hash %s: %v", relPath, err))
			continue
		}

		if actual != expected {
			failures = append(failures, fmt.Sprintf("Modified: %s", relPath))
		}
	}

	if len(failures) > 0 {
		return fmt.Errorf("File integrity check failed:\n%s", strings.Join(failures, "\n"))
	}
	return nil
}

func generateVersionStatusFile() {
	cmd := exec.Command("/usr/local/bin/python3", "app/services/scheduler/version_check.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = append(os.Environ(), "PYTHONPATH=/grylli")
	err := cmd.Run()
	if err != nil {
		log.Printf("[entrypoint]  Failed to write version_status.json: %v", err)
	} else {
		log.Println("[entrypoint] version_status.json written successfully")
	}
}

func main() {
	fmt.Println("Grylli Entrypoint: Verifying file integrity...")

	if err := checkIntegrity(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	fmt.Println("Integrity verified. Starting Python app...")

	generateVersionStatusFile()

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
