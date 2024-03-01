package main

import (
	"encoding/json"
	"flag"
	"log"
	"net/http"

	"github.com/nats-io/nats.go"
)

// Define the structure for your JSON data
type Data struct {
	Name  string `json:"name"`
	Age   int    `json:"age"`
	Email string `json:"email"`
}

func main() {
	port := flag.Int("port", 5000, "Port on which to listen")
	natsServer := flag.String("nats-server", "nats://localhost:4222", "NATS server address")
	natsSubject := flag.String("nats-subject", "hello.world", "NATS subject to publish to")
	flag.Parse()

	http.HandleFunc("/v1/api", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Only POST method is allowed", http.StatusMethodNotAllowed)
			return
		}

		var data Data
		err := json.NewDecoder(r.Body).Decode(&data)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		// Here, you would add additional validation for the Data struct if needed

		nc, err := nats.Connect(*natsServer)
		if err != nil {
			log.Printf("Failed to connect to NATS server: %v", err)
			http.Error(w, "Failed to connect to NATS server", http.StatusInternalServerError)
			return
		}
		defer nc.Close()

		dataBytes, err := json.Marshal(data)
		if err != nil {
			http.Error(w, "Error encoding JSON", http.StatusInternalServerError)
			return
		}

		err = nc.Publish(*natsSubject, dataBytes)
		if err != nil {
			log.Printf("Failed to publish message: %v", err)
			http.Error(w, "Failed to publish message", http.StatusInternalServerError)
			return
		}

		log.Printf("Published message to %s: %+v", *natsSubject, data)
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{"message": "Data received and published successfully"})
	})

	log.Printf("Server starting on port %d...", *port)
	log.Fatal(http.ListenAndServe(":5000", nil))
}
