{{- range . -}}
{{- if not (regexMatch "^[a-z0-9][a-z0-9+._/@:-]*$" .) -}}
{{- fail (printf "Invalid package name: %q" .) -}}
{{- end }} {{ . }}
{{- end -}}
