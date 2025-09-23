## **4. Manifests (Normative)**

SpatialDDS manifests are JSON documents that provide descriptive metadata for resources referenced on the DDS bus. Manifests are
dereferenced through `spatialdds://` URIs (Section 3) and inform clients about coverage, capabilities, transports, security
requirements, and dependencies.

### **4.1 Common structure (Normative)**

Every manifest SHALL:

* Conform to UTF-8 encoded JSON.
* Include the members listed in Table 4-1.

| Member | Requirement | Description |
| --- | --- | --- |
| `self_uri` | REQUIRED | Canonical PID or RID for this manifest (Section 3.4). |
| `resource_id` | REQUIRED | ULID portion of the identifier matching the DDS field (e.g., `service_id`). |
| `resource_kind` | REQUIRED | One of `anchor`, `anchor-set`, `service`, or `content`. |
| `profile_ids` | REQUIRED | Array of profile identifiers implemented by this resource. At minimum `core:1.0`. |
| `version` | REQUIRED | Provider-defined semantic or numeric version string. |
| `zone` | REQUIRED | Zone label corresponding to the URI path. |
| `authority` | REQUIRED | Domain name that issued the identifier. |
| `created_at` | REQUIRED | RFC 3339 timestamp of initial publication. |
| `updated_at` | REQUIRED | RFC 3339 timestamp of the latest revision. |
| `description` | OPTIONAL | Human-readable summary. SHOULD be ≤ 512 characters. |
| `capabilities` | REQUIRED for services/content | Array describing supported operations (see Section 4.2). |
| `coverage` | REQUIRED when applicable | Spatial coverage geometry or bounding volume describing availability. |
| `transports` | REQUIRED when endpoints exist | List of endpoint descriptors, each specifying scheme, host, port, and QoS hints. |
| `auth` | OPTIONAL | Authentication requirements (Section 7). |
| `dependencies` | OPTIONAL | Array of `spatialdds://` URIs that this resource depends on. |

If a resource has no physical coverage (for example, a global anchor registry), the `coverage` member SHALL be present with
`"kind": "global"`.

### **4.2 Resource-specific requirements (Normative)**

* **Anchors and Anchor Sets** SHALL include a `anchors` array or `anchor_sets` array. Each entry SHALL provide a GeoPose using the
  `frame_kind`, `lat_deg`, `lon_deg`, `alt_m`, and quaternion members defined in `idl/v1.3/anchors.idl`. Anchor manifests SHALL
  also provide a `stamp` indicating the most recent update and MAY reference supporting assets through the `assets` array.
* **Services** SHALL describe callable endpoints in `transports`. For DDS-based interactions the entry SHALL specify the topic
  names, QoS class (Section 6), and any required discovery parameters. HTTP or gRPC endpoints SHALL include the HTTP method and
  base path. Services SHALL declare supported request/response encodings via `capabilities[*].formats`.
* **Content** manifests SHALL list anchors or frames that the content binds to using the `bindings` array. Each binding SHALL
  reference a SpatialDDS anchor URI and MAY include placement offsets. Content manifests MAY include asset descriptors for large
  media; those descriptors MAY use HTTPS URLs or content-addressed URIs.

### **4.3 Validation and publication (Normative)**

Authorities SHALL validate manifests against the JSON Schemas published with this specification (see Appendix references). A
manifest revision SHALL be published whenever any REQUIRED member changes. Providers MAY publish additional metadata, but custom
members SHALL be namespaced using reverse-DNS keys (e.g., `"com.example:retention_days"`).

Manifests SHALL be made available via HTTPS as described in Section 3.3. When manifests include references to large artifacts or
non-public transports, the manifest SHALL state any authentication or licensing prerequisites in the `auth` section. Providers
SHOULD include sample request flows or OpenAPI references in `documentation` members when complex interactions are expected.

### **4.4 Examples (Informative)**

Representative manifests are provided for reference:

#### **4.4.1 Visual Positioning Service (VPS)**

```json
{{include:manifests/v1.3/vps_manifest.json}}
```

#### **4.4.2 Mapping Service**

```json
{{include:manifests/v1.3/mapping_service_manifest.json}}
```

#### **4.4.3 Content/Experience Package**

```json
{{include:manifests/v1.3/content_experience_manifest.json}}
```

#### **4.4.4 Anchor Set**

```json
{{include:manifests/v1.3/anchors_manifest.json}}
```
