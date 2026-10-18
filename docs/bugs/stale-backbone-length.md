# Docs kept a stale PVC cut length

**Where:** BOM / ASSEMBLY  
**Status:** fixed

| | |
|---|---|
| What | Docs said the right backbone is 583 mm; the model has 568 mm. |
| How found | Cross-check of docs against the build's cut list. |
| Cost | Would have cost a wrong PVC cut. |
| Root cause | Lengths were typed into docs by hand after an older version. |
| Fix | Docs corrected to 568 mm (PVC total 2.15 m). |
| What catches it now | Rule: cut lengths come from `split.build('frame')`'s cut list. Idea: a test that greps the docs for every cut length. |
