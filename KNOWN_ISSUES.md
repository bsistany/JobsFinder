# Known Issues & Backlog

## Known Issues

### KI-001: No conversational context between searches
**Status:** Open  
**Discovered:** Phase 2  
**Description:** Follow-up messages that reference a previous search lose the prior context.  
**Example:** User searches "cybersecurity jobs in Ottawa", then says "how about remote instead?" — Claude doesn't know what job title to carry over, resulting in an empty search.  
**Fix:** Planned for Phase 3 (conversation history).

### KI-002: I want to see the history (the last query) so I can edit it in place instead of always typing a brand new query
**Status:** Open  
**Discovered:** Phase 2  
**Description:** explained in the title
**Example:** User searches "cybersecurity jobs in Ottawa", then says "cybersecurity jobs in Toronto" but the previous query is visible and cane be edited
**Fix:** Planned for Phase 3 


---

## Backlog

- **Phase 3:** Conversational context — send chat history to the LLM so follow-up queries work naturally
- **Phase 4:** Cover letter / resume builder
