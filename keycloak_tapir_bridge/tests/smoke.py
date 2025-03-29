from google.cloud import pubsub_v1

def callback(message):
    print(f"[RECEIVED] {message.message_id}: {message.data.decode('utf-8')}")
    message.nack()
    exit(0)

def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path("arxiv-development", "keycloak-arxiv-events-sub")
    print("Listening on", subscription_path)

    future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        future.result()
    except KeyboardInterrupt:
        print("Stopping...")
        future.cancel()

if __name__ == '__main__':
    main()
