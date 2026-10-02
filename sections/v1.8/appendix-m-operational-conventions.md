## **Appendix M: Documented Operational Conventions (Informative)**

This appendix records two coordination patterns that are not new protocol — they use only existing types and QoS — but that recurred across the reference deployment and are worth writing down so independent implementations converge on the same shapes. Nothing here adds IDL or changes a normative requirement; the keyed-removal rule those patterns rely on is normative and lives in §2.14.

### M.1 Keyed commands with explicit declines

A command addressed to a specific participant is published on a shared keyed command topic, keyed by the addressee. The pattern has three parts:

- **Addressed commands.** The writer sets the key to the intended recipient and publishes the command instance. Every participant reads the topic, but a participant acts only on instances keyed to itself.
- **Decline with reason.** When an addressee cannot or will not carry out a command, it does not stay silent: it publishes a response carrying a terminal state and a human-readable reason (the same final-sample-then-dispose discipline as §2.14 when the command instance is latched). A decline is a first-class, observable outcome, not an absence.
- **Silence for other keys.** A participant publishes nothing for instances keyed to others. Silence on another key is not a decline and carries no meaning — only an addressed response does.

The value of the pattern is that a late joiner or an observer can always distinguish *refused* from *not-yet-answered* from *not-for-me*, because the first is an explicit sample, the second is a pending instance, and the third is simply a key the participant never writes.

### M.2 Shared multi-writer lanes

A single topic sometimes carries contributions from several writers at once — a shared "lane" rather than one writer per topic. The pattern that kept this unambiguous in practice:

- **Several writers, addressed readers.** Many participants write to the lane; readers filter to the instances they care about by key, exactly as in M.1.
- **One writer per key for physical-thing entities.** When an instance represents a physical thing — an entity binding, a tracked object, a device's own state — exactly one writer owns that key at a time. Multiple writers MAY share the lane, but they MUST NOT concurrently write the same physical-thing key, because two writers describing one physical thing produce contradictions no reader can reconcile.
- **Ownership transfer is explicit.** Handing a physical-thing key from one writer to another follows the §2.14 removal discipline: the outgoing writer publishes a terminal sample and disposes the instance before the incoming writer takes the key, so the transfer is observable rather than a race.

Logical or aggregate instances (summaries, derived views) MAY be written by several writers without the one-writer-per-key rule, since they do not assert the state of a single physical thing.
