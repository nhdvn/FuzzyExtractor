package main

import (
	"bufio"
	"crypto/sha256"
	"fmt"
	"io"
	"math/rand"
	"os"
	"runtime"
	"sync"
	"time"

	"github.com/lukechampine/fastxor"
)

const B = 126
const S = 80
const N = 28
const R = 18
const K = 16
const P = 12

func lock_function(key, value []byte) []byte {

	nonce := make([]byte, R)
	rand.Read(nonce)

	hash := sha256.New224()
	hash.Write(nonce)
	hash.Write(key)
	vlock := hash.Sum(nil)

	fastxor.Bytes(vlock, vlock, value)

	return append(vlock, nonce...)
}

func is_zero(bytes []byte) bool {

	b := byte(0)

	for _, s := range bytes {
		b |= s
	}

	return b == 0
}

func unlock_function(key, data []byte) []byte {

	vlock, nonce := data[:N], data[N:]

	hash := sha256.New224()
	hash.Write(nonce)
	hash.Write(key)
	value := hash.Sum(nil)

	fastxor.Bytes(value, value, vlock)

	if is_zero(value[K:]) {
		return value[:K]
	}

	return nil
}

const routine = 5
const bound = 90000000 / routine

func worker_gen(nth int, biostr string, secret []byte, handler *sync.WaitGroup) {

	index := make([]byte, S)
	subset := make([]byte, S)

	helper := fmt.Sprintf("./test/%d", nth)
	output, _ := os.Create(helper)

	defer output.Close()
	defer handler.Done()

	for i := 0; i < bound; i++ {

		rand.Read(index)
		for k, v := range index {
			subset[k] = biostr[v]
		}

		vlock := lock_function(subset, secret)
		output.Write(index)
		output.Write(vlock)
	}

	fmt.Printf("worker %d done \n", nth)
}

func worker_rep(nth int, biostr string, handler *sync.WaitGroup) {

	subset := make([]byte, S)
	buffer := make([]byte, B)

	helper := fmt.Sprintf("./test/%d", nth)
	output, _ := os.Open(helper)
	reader := bufio.NewReader(output)

	defer output.Close()
	defer handler.Done()

	for i := 0; i < bound; i++ {

		_N, _ := io.ReadFull(reader, buffer)

		if _N != 126 {
			fmt.Println("Error Reader")
		}

		index := buffer[:S]
		vlock := buffer[S:]

		for k, v := range index {
			subset[k] = biostr[v]
		}

		secret := unlock_function(subset, vlock)

		if secret != nil {
			fmt.Printf("worker %d found secret\n", nth)
			fmt.Println(secret)
			break
		}
	}

	fmt.Printf("worker %d done \n", nth)
}

func key_generate(biostr string) {

	secret := make([]byte, K)
	rand.Read(secret)
	fmt.Println(secret)

	zeros := make([]byte, P)
	secret = append(secret, zeros...)

	var handler sync.WaitGroup

	for i := 0; i < routine; i++ {
		handler.Add(1)
		go worker_gen(i, biostr, secret, &handler)
	}

	handler.Wait()
}

func key_reproduce(biostr string) {

	var handler sync.WaitGroup

	for i := 0; i < routine; i++ {
		handler.Add(1)
		go worker_rep(i, biostr, &handler)
	}

	handler.Wait()
}

func sample_then_lock(bio_1, bio_2 string) {

	fmt.Println("Start Enrollment")
	key_generate(bio_1)

	fmt.Println("Start Verification")
	key_reproduce(bio_2)
}

func main() {

	runtime.GOMAXPROCS(4)

	rand.Seed(time.Now().UnixNano())

	input, err := os.Open("test.txt")

	if err != nil {
		fmt.Println("No File Exist")
		return
	}

	defer input.Close()

	scanner := bufio.NewScanner(input)
	var lines []string

	for scanner.Scan() {
		lines = append(lines, scanner.Text())
	}

	sample_then_lock(lines[0], lines[1])
}
