# Assembly animations showed an impossible build

**Where:** Assembly guide (docs/ASSEMBLY.md)  
**Status:** fixed

| | |
|---|---|
| What | Parts slid in along pivot axes *through* fork plates, screws went in from the wrong side, bearing/spacer stacks floated in the air before their holder existed, and the shoulder-rest pins were all added at the end (the pieces would fall off). |
| How found | User review of the step GIFs. |
| Cost | None printed; a builder following the GIFs would have been confused or stuck. |
| Root cause | Insertion directions and build order were taken from the model tree, not from how a person holds the parts. |
| Fix | Holder first, then what it holds; sub-assemblies built at a staging spot and carried in; each fastener enters from its head side; each rest piece pinned as it goes on. |
| What catches it now | Not automated. Review rule in LESSONS (assembly animation rows). Idea: a check that every part appearing in a step touches a part already placed. |
