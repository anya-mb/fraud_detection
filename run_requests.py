import requests
import json
import time
import numpy as np
from threading import Thread


# Function to send a POST request with randomized payload
def send_request():
    url = "https://aynlrqq5q9.execute-api.us-east-1.amazonaws.com/transaction"
    payload = {
        "rooms": np.random.randint(1, 6),  # Random integer between 1 and 5
        "area": np.random.randint(10, 201),  # Random integer between 10 and 200
        "floor": np.random.randint(1, 26),  # Random integer between 1 and 25
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(response.text)  # Optional: print response for debugging


# Main logic to send requests over 10 minutes with variable delay and count
def main():
    start_time = time.time()
    while time.time() - start_time < 600:  # 10 minutes
        # Calculate the number of invocations for this second
        invocations = np.random.poisson(20)  # Poisson distribution around mean 20
        # Introduce sudden spikes randomly
        if np.random.rand() < 0.1:  # 10% chance of spike
            invocations = min(invocations + np.random.randint(50, 101), 100)

        # Send the calculated number of requests
        threads = []
        for _ in range(invocations):
            thread = Thread(target=send_request)
            thread.start()
            threads.append(thread)
            time.sleep(
                np.random.uniform(0, 1.0 / invocations)
            )  # Spread requests within the second

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Wait until the start of the next second
        time.sleep(max(0, 1.0 - (time.time() % 1)))


if __name__ == "__main__":
    main()
