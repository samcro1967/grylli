package main

import (
	"fmt"
	"net/http"
	"os"
	"strings"
)

func main() {
	baseURL := os.Getenv("BASE_URL")
	if baseURL == "" {
		baseURL = "/grylli"
	}
	baseURL = strings.TrimRight(baseURL, "/")

	url := fmt.Sprintf("http://127.0.0.1:5069%s/status/", baseURL)

	// Create client that does NOT follow redirects
	client := &http.Client{
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	resp, err := client.Get(url)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Request failed: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		fmt.Fprintf(os.Stderr, "❌ Unexpected status: %d for URL %s\n", resp.StatusCode, url)
		os.Exit(1)
	}

	fmt.Println("✅ Healthcheck passed:", url)
}
