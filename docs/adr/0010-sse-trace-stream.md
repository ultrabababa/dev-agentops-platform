# Use SSE for the V1 Trace Stream

V1 will expose live trace events with server-sent events rather than WebSockets. Triage runs need a mostly one-way progress stream from backend to dashboard, so SSE provides a simpler browser-native fit; WebSockets are deferred until the product needs bidirectional interactions such as mid-run human approval, interruption, plan editing, or multi-user collaboration.
