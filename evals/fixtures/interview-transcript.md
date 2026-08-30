# Mock interview transcript: "Design a chat system" (candidate performance to grade)

Interviewer: Let's design a chat system like WhatsApp. Where would you like to start?

Candidate: Sure. So for a chat system I would use microservices. First, the client sends a message to an API gateway, which routes to the message service. I'd use MongoDB for messages because it scales horizontally, and WebSockets for real-time delivery.

Interviewer: What scale are you designing for?

Candidate: WhatsApp-scale, so like a billion users. With MongoDB sharded by user ID it will handle that fine. Kafka would sit between the gateway and the message service to decouple everything.

Interviewer: How do you decide what to build first if this were a new product?

Candidate: I'd start with the full architecture because rearchitecting later is expensive. Set up Kubernetes from day one so scaling is automatic.

Interviewer: Walk me through delivering a message from user A to user B.

Candidate: A sends to the gateway, gateway publishes to Kafka, consumer writes to Mongo, then pushes to B's WebSocket connection. If B is offline, the message waits in Mongo and gets delivered on reconnect.

Interviewer: What's the consistency model for delivery receipts — sent, delivered, read?

Candidate: Eventual consistency is fine, that's what NoSQL gives us.

Interviewer: What happens when one user has 10 million followers and sends a message to a channel?

Candidate: Kafka handles it, it's very high throughput.

Interviewer: A message shows up twice for user B. Where did that come from?

Candidate: Probably a network glitch. The client can deduplicate by message ID.

Interviewer: Let's say the primary Mongo shard goes down during peak traffic.

Candidate: MongoDB has automatic failover with replica sets, so it just works.

Interviewer: Last one — where does this system lie on CAP, and does that match what a chat user expects?

Candidate: It's AP, which is the right choice for chat. Users care about availability.

Interviewer: OK, we're out of time. Anything to add?

Candidate: I think I covered the main components — gateway, Kafka, Mongo, Kubernetes. Happy to go deeper on any part.
