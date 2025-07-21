// ---------------------------------------------------------------------
// entrypoint.go
// Project root
// Compiled container entrypoint. Verifies file integrity using SHA-256
// against file_hashes.sha256 and exits if tampering is detected.
// ---------------------------------------------------------------------

package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

var (
	hashFile = "file_hashes.sha256"

	// Optional files allowed to be missing in production containers
	optionalFiles = map[string]bool{
		"scripts/generate_screenshots.py": true,
		"scripts/init_db.py":              true,
	}
)

// computeHash calculates SHA-256 hash of the given file
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

// checkIntegrity parses file_hashes.sha256 and compares hashes to actual files
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

// main verifies integrity and starts the Python application
func main() {
	fmt.Println("🔒 Grylli Entrypoint: Verifying file integrity...")

	if err := checkIntegrity(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	fmt.Println("Integrity verified. Starting Python app...")

	// Run the main application (adjust path if needed)
	err := exec.Command("/usr/bin/python3", "/grylli/wsgi.pyc").Run()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to start app: %v\n", err)
		os.Exit(1)
	}
}
