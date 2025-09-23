## **9. Appendices (Informative)**

Supplemental material is organized into separate documents referenced below. These appendices provide detailed schemas, extended
examples, and rationale that complement the normative sections of this specification.

### **9.1 Example IDLs**

* [Appendix A: Core Profile 1.0](appendix-a.md)
* [Appendix B: Discovery Profile 1.0](appendix-b.md)
* [Appendix C: Anchor Registry Profile 1.0](appendix-c.md)
* [Appendix D: Extension Profiles](appendix-d.md)
* [Appendix E: Provisional Extension Examples](appendix-e.md)

### **9.2 Extended manifests and samples**

* [Operational scenarios and deployment patterns](04-operational-scenarios.md)
* Additional JSON manifest samples are available in the `manifests/v1.3` directory referenced throughout Section 4.

### **9.3 Schema references**

JSON Schemas for manifests, discovery messages, and capability descriptors are distributed alongside this specification in the
`scripts/schema` directory. Providers SHOULD incorporate these schemas into their CI pipelines to ensure manifests remain
conformant.

### **9.4 Rationale and future work**

* [Conclusion](conclusion.md)
* [Future directions](future-directions.md)
* [Glossary of acronyms](glossary.md)
* [References](references.md)

These documents capture background context and design decisions, including why SpatialDDS adopts resolver-friendly URIs and how
it aligns with adjacent standards. They are informative and do not introduce new conformance requirements.
