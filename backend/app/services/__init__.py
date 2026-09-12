# Business logic that's reused across routers (and later, across pipeline jobs)
# goes here — e.g. notification dispatch logic, subscription matching.
# Keeps routers thin: a router should parse the request, call a service, return
# the response — not contain business logic itself.
