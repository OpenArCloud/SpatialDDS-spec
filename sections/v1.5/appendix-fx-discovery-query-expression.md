## **Appendix F.X Discovery Query Expression (Informative)**

This appendix defines the boolean filter grammar used by the deprecated `disco.CoverageQuery.expr`. The language is case-sensitive,
UTF-8, and whitespace-tolerant. Identifiers target announced metadata fields (for example `type`, `profile`,
`module_id`); string literals are double-quoted and use a C-style escape subset.

```abnf
expr       = or-expr
or-expr    = and-expr *( WS "||" WS and-expr )
and-expr   = unary-expr *( WS "&&" WS unary-expr )
unary-expr = [ "!" WS ] primary
primary    = comparison / "(" WS expr WS ")"
comparison = ident WS op WS value
op         = "==" / "!="
ident      = 1*( ALPHA / DIGIT / "_" / "." )
value      = string
string     = DQUOTE *( string-char ) DQUOTE
string-char= %x20-21 / %x23-5B / %x5D-10FFFF / escape
escape     = "\\" ( DQUOTE / "\\" / "n" / "r" / "t" )
WS         = *( SP / HTAB )

; Notes:
; - Identifiers address announced metadata fields (e.g., "type", "profile", "module_id").
; - Values are double-quoted strings; escapes follow C-style subset.
; - Operators: equality and inequality only. Boolean ops: &&, ||, unary !
; - Parentheses group precedence; otherwise, ! > && > ||
; - Comparisons are exact string matches; wildcards/globs are not supported.
; - Unknown identifiers evaluate to false in comparisons.
```
