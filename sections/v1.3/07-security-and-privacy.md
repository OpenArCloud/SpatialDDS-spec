## **7. Security and Privacy (Normative + Informative)**

SpatialDDS deployments SHALL protect identifiers, manifests, and data-plane exchanges commensurate with the sensitivity of the
information being shared. This section defines baseline security requirements and provides guidance for privacy-preserving
implementations.

### **7.1 Authentication and authorization (Normative)**

* HTTPS resolver endpoints SHALL use TLS 1.2 or later with modern cipher suites. Client authentication MAY use OAuth 2.0 Bearer
  tokens, mutual TLS (mTLS), or other enterprise mechanisms advertised in manifests.
* Services that require authenticated access SHALL describe accepted mechanisms in the manifest `auth` block. Supported keys
  include `"scheme": "oauth2"`, `"scheme": "mtls"`, or `"scheme": "api-key"`. When OAuth 2.0 / OIDC is used, manifests SHALL
  provide the issuer URL and scopes needed to obtain tokens.
* DDS transport security SHOULD employ DDS Security (OMG DDS Security specification) with mutual authentication. Keys SHALL be
  rotated according to organizational policy and SHOULD be scoped per zone when feasible.
* Authorization decisions SHOULD be enforced as close to the resource as possible (e.g., at the resolver or DDS participant). The
  manifest MAY include capability-based access hints (e.g., `"allowed_roles": ["anchor-admin"]`).

### **7.2 Integrity and signing (Normative)**

* Manifests SHALL include integrity metadata. Providers MAY use JSON Web Signatures (JWS) or CBOR Object Signing and Encryption
  (COSE). When signing is applied, a `signature` object SHALL be present containing the algorithm, key identifier, and detached or
  embedded signature.
* Anchor sets or other critical data MAY be signed at the payload level. When provided, the manifest SHALL specify the signing
  method so consumers can validate updates before acceptance.

### **7.3 Privacy considerations (Informative)**

Spatial data can reveal personal or sensitive information. Implementers SHOULD:

* Minimize inclusion of personally identifiable information in manifests and announcements.
* Respect jurisdictional requirements for location sharing and consent. Manifest `auth` blocks MAY reference policy documents or
  data-retention statements.
* Clearly state retention periods for stored anchors, pose histories, and perception data. The manifest MAY include custom fields
  such as `"com.example:retention_days"` to communicate policy.
* Provide mechanisms to revoke anchors or content rapidly (e.g., publish `ttl_ms = 0` announcements and serve `410 Gone`).

### **7.4 Transport security (Normative)**

* All HTTPS endpoints SHALL enforce TLS certificate validation and SHALL prefer HTTP Strict Transport Security (HSTS).
* WebRTC transports SHALL require DTLS-SRTP encryption.
* DDS transports SHALL enable encryption-at-rest when the deployment infrastructure supports it (e.g., encrypted DDS shared
  memory segments).

### **7.5 Operational guidance (Informative)**

Operators SHOULD monitor for resolver misuse, repeated authentication failures, and stale manifests. Security incidents SHOULD
trigger manifest revocation (`410 Gone`) and publication of updated identifiers. Privacy impact assessments are RECOMMENDED for
deployments involving public spaces or user-generated anchors.
