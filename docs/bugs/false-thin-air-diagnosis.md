# False diagnosis: "the lock screw lands in thin air"

**Where:** my analysis of [rest-bracket-attachment](rest-bracket-attachment.md) (a process bug, not a part)  
**Status:** fixed (claim corrected; test calibrated)

| | |
|---|---|
| What | I said the old rest lock screw went into empty space past the tower's slanted edge, and that the new fastener test "confirmed" it (2 mm grip). In fact the front plate and a nut pocket were right there (picture in [rest-bracket-attachment](rest-bracket-attachment.md), panel B). |
| How found | Drawing the picture the user asked for: the section showed the nut in its pocket. |
| Cost | A wrong story about why the tower was bad; it nearly drove a reprint. |
| Root cause | (1) My probe sampled points *on* the screw's axis, which is the hole, so it found nothing. (2) The first version of the test counted only printed plastic as grip, not the nut the screw goes into, and I trusted it without running it on a known-good case. |
| Fix | The test now counts nuts and inserts and samples a ring just outside the shank. Run on the old design (archive v54) and the new assembly: both 0 failing; the old screw shows 6 mm. |
| What catches it now | Rule: a new test must be run on a known-good and a known-bad case before its result is believed. Show a section picture before declaring a geometry bug. |
