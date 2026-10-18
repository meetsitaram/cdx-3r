# Lift carriage over-stressed under an M8 pivot nut (stress test, open)

**Where:** lift carriage (10), seat of the M8 nyloc of a lift-link pivot  
**Status:** open: first-pass FEA finding, to confirm

| | |
|---|---|
| What | With 150 N hanging from the abduction housing, the PETG under the M8 nyloc nut of a lift-link pivot on the carriage reaches ~47 MPa (safety factor 0.64; printed PETG yields ~30 MPa layer-to-layer). |
| How found | Fusion Static Stress of the whole girdle ([docs/stress](../stress/README.md)). |
| Cost | Carriage already printed. |
| Root cause | The nut bears on a small plastic seat; the whole arm load goes through that pivot. |
| Fix | Open. Confirm with separation contacts (bonded contacts exaggerate nut-edge peaks); if real: washer under the nut, bigger seat. |
| What catches it now | Nothing automatic; the stress studies are run by hand (docs/stress). |
