package main

import (
	"crypto/md5"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/sha512"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/nats-io/nats.go"
	"golang.org/x/crypto/sha3"
)

const (
	LogLevelNormal = iota
	LogLevelDebug
)

var currentLogLevel = LogLevelNormal

// Request represents the incoming request payload
type Request struct {
	HashType string `json:"hash_type"`
	Data     string `json:"data"`
}

// Response represents the payload to be returned to the requester
type Response struct {
	RequestID  string `json:"request_id"`
	HashType   string `json:"hash_type"`
	HashedData string `json:"hashed_data"`
}

// CacheEntry stores individual cache items with their timestamp
type CacheEntry struct {
	HashedData string
	Timestamp  time.Time
}

// HashCache manages the cache for hashed data
type HashCache struct {
	entries map[string]CacheEntry
	timeout time.Duration
	mutex   sync.Mutex
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}

func logMessage(level int, message string) {
	if level <= currentLogLevel {
		log.Println(message)
	}
}

func logDebug(message string) {
	logMessage(LogLevelDebug, message)
}

// NewHashCache initializes a new hash cache
func NewHashCache(timeout time.Duration) *HashCache {
	return &HashCache{
		entries: make(map[string]CacheEntry),
		timeout: timeout,
	}
}

// Add inserts a new hash data entry into the cache
func (hc *HashCache) Add(key, hashedData string) {
	hc.mutex.Lock()
	defer hc.mutex.Unlock()

	hc.entries[key] = CacheEntry{
		HashedData: hashedData,
		Timestamp:  time.Now(),
	}
}

// Get retrieves hashed data from the cache if available and not expired
func (hc *HashCache) Get(key string) (string, bool) {
	hc.mutex.Lock()
	defer hc.mutex.Unlock()

	entry, exists := hc.entries[key]
	if !exists || time.Since(entry.Timestamp) > hc.timeout {
		return "", false
	}

	return entry.HashedData, true
}

// hashData hashes the given data using the specified hash type
func hashData(hashType, data string) (string, error) {
	decodedData, err := base64.StdEncoding.DecodeString(data)
	if err != nil {
		return "", err
	}

	var hashedData []byte
	switch hashType {
	case "MD5":
		sum := md5.Sum(decodedData)
		hashedData = sum[:]
	case "SHA-1":
		sum := sha1.Sum(decodedData)
		hashedData = sum[:]
	case "SHA-224":
		sum := sha256.Sum224(decodedData)
		hashedData = sum[:]
	case "SHA-256":
		sum := sha256.Sum256(decodedData)
		hashedData = sum[:]
	case "SHA-512/224":
		sum := sha512.Sum512_224(decodedData)
		hashedData = sum[:]
	case "SHA-512/256":
		sum := sha512.Sum512_256(decodedData)
		hashedData = sum[:]
	case "SHA-384":
		sum := sha512.Sum384(decodedData)
		hashedData = sum[:]
	case "SHA-512":
		sum := sha512.Sum512(decodedData)
		hashedData = sum[:]
	case "SHA3-224":
		sum := sha3.Sum224(decodedData)
		hashedData = sum[:]
	case "SHA3-256":
		sum := sha3.Sum256(decodedData)
		hashedData = sum[:]
	case "SHA3-384":
		sum := sha3.Sum384(decodedData)
		hashedData = sum[:]
	case "SHA3-512":
		sum := sha3.Sum512(decodedData)
		hashedData = sum[:]
	default:
		return "", fmt.Errorf("unsupported hash type: %s", hashType)
	}

	return hex.EncodeToString(hashedData[:]), nil
}

func main() {
	// Configurations with environment variables
	natsURL := getEnv("NATS_URL", nats.DefaultURL)
	requestSubject := getEnv("REQUEST_SUBJECT", "hash_requests")
	logLevelEnv := getEnv("LOG_LEVEL", "normal")
	natsUser := getEnv("NATS_USER", "")
	natsPassword := getEnv("NATS_PASSWORD", "")

	// Set log level based on environment variable
	if logLevelEnv == "debug" {
		currentLogLevel = LogLevelDebug
	} else {
		currentLogLevel = LogLevelNormal
	}

	// Connect to NATS server
	var opts []nats.Option

	// Add authentication options if username and password are set
	if natsUser != "" && natsPassword != "" {
		opts = append(opts, nats.UserInfo(natsUser, natsPassword))
	}

	// Connect to NATS with the specified options
	nc, err := nats.Connect(natsURL, opts...)
	if err != nil {
		log.Fatal(err)
	}
	defer nc.Close()

	logDebug("Debug logging enabled")

	// Initialize the hash cache with a 5-minute timeout
	cache := NewHashCache(5 * time.Minute)

	// Subscribe to hash requests
	nc.QueueSubscribe(requestSubject, "workers", func(msg *nats.Msg) {
		var req Request
		if err := json.Unmarshal(msg.Data, &req); err != nil {
			log.Printf("Error unmarshalling request: %v", err)
			return
		}

		logDebug(fmt.Sprintf("Received request: %+v", req))

		// Generate a cache key
		cacheKey := req.HashType + ":" + req.Data

		// Attempt to retrieve the hashed data from cache
		if cachedData, found := cache.Get(cacheKey); found {
			logDebug(fmt.Sprintf("Cache hit for key: %s", cacheKey))
			response := Response{
				RequestID:  uuid.New().String(),
				HashType:   req.HashType,
				HashedData: cachedData,
			}
			if responseData, err := json.Marshal(response); err == nil {
				msg.Respond(responseData)
				logDebug(fmt.Sprintf("Sent cached response: %+v", response))
			}
			return
		}

		// Hash the data
		hashedData, err := hashData(req.HashType, req.Data)
		if err != nil {
			log.Printf("Error hashing data: %v", err)
			return
		}

		// Cache the hashed data
		cache.Add(cacheKey, hashedData)
		logDebug(fmt.Sprintf("Added to cache: %s", cacheKey))

		// Respond with the hashed data
		response := Response{
			RequestID:  uuid.New().String(),
			HashType:   req.HashType,
			HashedData: hashedData,
		}
		if responseData, err := json.Marshal(response); err == nil {
			msg.Respond(responseData)
			logDebug(fmt.Sprintf("Sent response: %+v", response))
		}
	})

	log.Printf("Listening for hash requests on '%s' subject...", requestSubject)
	select {} // Keep the application running
}
