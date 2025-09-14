## **Appendix B: Discovery Profile 1.0**

*The Discovery profile defines the lightweight announce messages and manifests that allow services, coverage areas, and spatial content or experiences to be discovered at runtime. It enables SpatialDDS deployments to remain decentralized while still providing structured service discovery.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS Discovery 1.2
// Lightweight announces for services, coverage, and content

module spatial {
  module disco {

    typedef spatial::core::Time Time;

    enum ServiceKind {
      VPS = 0,
      MAPPING = 1,
      RELOCAL = 2,
      SEMANTICS = 3,
      STORAGE = 4,
      CONTENT = 5,
      ANCHOR_REGISTRY = 6,
      OTHER = 255
    };

    @appendable struct KV {
      string key;
      string value;
    };

    @appendable struct ServiceAnnounce {
      @key string service_id;
      string name;
      ServiceKind kind;
      string version;
      string org;
      sequence<string,16> rx_topics;
      sequence<string,16> tx_topics;
      sequence<KV,32> hints;
      string manifest_uri;
      string auth_hint;
      Time stamp;
      uint32 ttl_sec;
    };

    @appendable struct CoverageHint {
      @key string service_id;
      sequence<string,64> geohash;
      double bbox[4];           // [min_lon, min_lat, max_lon, max_lat]
      double center_lat; double center_lon; double radius_m;
      Time stamp;
      uint32 ttl_sec;
    };

    @appendable struct ContentAnnounce {
      @key string content_id;
      string provider_id;
      string title;
      string summary;
      sequence<string,16> tags;
      string class_id;
      string manifest_uri;
      double center_lat; double center_lon; double radius_m;
      Time available_from;
      Time available_until;
      Time stamp;
      uint32 ttl_sec;
    };

  }; // module disco
};
```
