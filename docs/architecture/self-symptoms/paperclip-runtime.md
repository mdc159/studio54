Hey Donna, can you help check your Paperclip wiring?

Read-only verification task. Do not modify anything.

Validate the current Paperclip runtime contract on Donna.

Check and report:

1. Whether /paperclip/instances/default/config.json exists and is readable
2. Whether the live Paperclip listener matches the declared host/port contract
3. Whether /api/health succeeds on the declared Paperclip endpoint
4. Whether PAPERCLIP_HERMES_GATEWAY_SOCKET is declared
5. If declared, whether the socket file exists and accepts connections
6. Whether the observed runtime matches the declared contract exactly

Output:
- Declared contract
- Observed runtime
- Mismatches
- Pass/fail summary
