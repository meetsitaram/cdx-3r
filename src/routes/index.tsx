import { createFileRoute } from "@tanstack/react-router";
import { useState, type ReactNode } from "react";
import { SiteNav } from "@/components/cdx/nav";
import { CadViewer } from "@/components/cdx/cad-viewer";
import { Button } from "@/components/ui/button";
import {
  BOM,
  CAD_STAGES,
  COST_TIERS,
  ELBOW_BUY,
  ELBOW_HUMAN,
  ELBOW_PHYSICS,
  ELBOW_PREVIEWS,
  ELBOW_PRINT,
  ELBOW_SWATCHES,
  SHOULDER_BUY,
  SHOULDER_PHYSICS,
  SHOULDER_PREVIEWS,
  SHOULDER_PRINT,
  SHOULDER_SWATCHES,
  PACK_BUY,
  PACK_PHYSICS,
  PACK_PREVIEWS,
  PACK_PRINT,
  PACK_SWATCHES,
  SYSTEM_PHYSICS,
  SYSTEM_PREVIEWS,
  SYSTEM_PRINT,
  SYSTEM_SWATCHES,
  GALLERY,
  MOTION,
  SPONSOR_SPLIT,
  STATS,
} from "@/lib/cdx";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return (
    <div id="top" className="min-h-screen bg-bg text-fg">
      <SiteNav />
      <Hero />
      <StatsStrip />
      <System />
      <Physics />
      <Cables />
      <Cad />
      <Motion />
      <Safety />
      <Gallery />
      <Cost />
      <Sponsor />
      <footer className="border-t border-border px-4 py-10 text-center text-xs text-subtle sm:px-6">
        CDX-3R concept design. Reference architecture, not a certified build.
        Structural analysis, e-stop testing, and battery safety review still required.
      </footer>
    </div>
  );
}

function Hero() {
  return (
    <section className="relative min-h-[78vh] overflow-hidden">
      <img
        src="/gallery/hero.jpg"
        alt="CDX-3R right-arm exoskeleton holding an industrial crate"
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-bg via-bg/55 to-bg/20" />
      <div className="relative mx-auto flex min-h-[78vh] max-w-6xl flex-col justify-end px-4 pb-14 pt-28 sm:px-6">
        <p className="mb-3 font-mono text-[11px] tracking-[0.28em] text-accent uppercase">
          Cable-driven · 3 revolute · right arm
        </p>
        <h1 className="max-w-3xl font-display text-5xl leading-[0.95] tracking-tight text-fg sm:text-7xl">
          Armor that
          <br />
          carries the load.
        </h1>
        <p className="mt-5 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
          CDX-3R is three powered revolute joints on the right arm — not a 7-DOF
          industrial manipulator. Motors in the backpack, Bowden cables to the
          joints, plates that read as armor. Left hand stays free for the kill
          switch.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a href="#gallery">
            <Button>View gallery</Button>
          </a>
          <a href="#sponsor">
            <Button variant="ghost">Sponsor kit</Button>
          </a>
        </div>
      </div>
    </section>
  );
}

function StatsStrip() {
  return (
    <section className="border-y border-border bg-surface">
      <div className="mx-auto grid max-w-6xl grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        {STATS.map((s, i) => (
          <div
            key={s.k}
            className={cn(
              "px-4 py-5",
              i !== 0 && "border-t border-border sm:border-t-0 sm:border-l",
              i === 1 && "sm:border-l",
              i >= 2 && "lg:border-l",
            )}
          >
            <div className="font-mono text-[10px] tracking-[0.22em] text-subtle uppercase">{s.k}</div>
            <div className="mt-1 font-display text-xl tracking-wide text-fg">{s.v}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Section({
  id,
  kicker,
  title,
  children,
}: {
  id: string;
  kicker: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-20 border-b border-border">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
        <p className="font-mono text-[11px] tracking-[0.28em] text-accent uppercase">{kicker}</p>
        <h2 className="mt-2 max-w-2xl font-display text-4xl tracking-tight text-fg sm:text-5xl">{title}</h2>
        <div className="mt-10">{children}</div>
      </div>
    </section>
  );
}

function System() {
  return (
    <Section id="system" kicker="01 — Architecture" title="Motors on the back. Torque at the joints.">
      <div className="grid gap-10 lg:grid-cols-2 lg:gap-16">
        <div className="space-y-5 text-base leading-relaxed text-muted">
          <p>
            A single shoulder motor is a demo, not a suit. The glenohumeral joint
            needs two powered planes for a crate you actually walk with: flexion
            to lift, abduction to clear the hip. Elbow flexion is the third axis.
            Rotation stays mostly passive so the mechanism does not fight you.
          </p>
          <p>
            Distal mass kills wearability. CDX-3R puts the three winches, clutches,
            and the 48 V sled in a backpack. Thick Bowden housings run over the
            right shoulder. The arm only carries pulleys, hard stops, and plates.
          </p>
          <p>
            The name is the kinematics. 3R = three revolute axes: shoulder flexion,
            shoulder abduction, elbow flexion. A 7R arm would add wrist roll, pitch,
            and yaw. Those stay passive here so the hand can still square on a crate
            without the mechanism fighting you.
          </p>
          <p>
            The plates are not costume first. They give the cables a stiff moment
            arm and spread load into the harness instead of through biceps and
            rotator cuff. Armor is the structure.
          </p>
        </div>
        <figure className="overflow-hidden rounded-xl">
          <img
            src="/gallery/pack.jpg"
            alt="Cutaway of the CDX-3R backpack with three winch modules"
            className="aspect-video w-full object-cover"
          />
          <figcaption className="mt-3 text-sm text-subtle">
            Pack cutaway — three actuation modules, battery sled, cable comb.
          </figcaption>
        </figure>
      </div>
      <div className="mt-12 grid gap-4 sm:grid-cols-3">
        {[
          ["Shoulder flexion", "Primary lift. Longest moment arm when the crate is out in front."],
          ["Shoulder abduction", "Clears the hip. Second sheave so a side swing does not pinch."],
          ["Elbow flexion", "Closes the arm. Antagonist pair so lowering is not a drop."],
        ].map(([t, d]) => (
          <article key={t} className="rounded-lg border border-border bg-surface p-5">
            <h3 className="font-display text-lg tracking-wide text-fg">{t}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">{d}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}

function Physics() {
  return (
    <Section id="physics" kicker="02 — Physics" title="The crate does not get lighter.">
      <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5 text-base leading-relaxed text-muted">
          <p>
            Lifting is joint torque against gravity. Weight acts at the load’s
            center of mass. That force creates a moment at the shoulder and elbow:
          </p>
          <p className="rounded-md border border-border bg-elevated px-4 py-3 font-mono text-sm text-fg">
            τ_load = r × F_g &nbsp;&nbsp; F_g = m g
          </p>
          <p>
            Motors add assistive torque in the same direction your muscles would.
            Net muscle demand becomes τ_muscle = τ_load − τ_exo. If the exo
            supplies most of the load torque, fatigue drops. The mass is unchanged.
            The path of the force is what changed.
          </p>
          <p>
            On a cable drive the motor never sits at the joint. A winch tension T
            on a pulley of radius r becomes the same torque: τ = T × r. Shorten
            the flexor cable, pay out the extensor, the joint rotates. That is the
            whole machine.
          </p>
        </div>
        <aside className="rounded-xl border border-border bg-surface p-6">
          <h3 className="font-display text-xl tracking-wide text-fg">What the exo actually does</h3>
          <ul className="mt-4 space-y-4 text-sm leading-relaxed text-muted">
            <li>
              <span className="font-medium text-fg">Adds joint torque.</span> External
              motors fight gravity’s moment so tissue does not have to.
            </li>
            <li>
              <span className="font-medium text-fg">Reroutes the load path.</span>{" "}
              Straps and rigid links dump crate weight into the harness and pack
              frame.
            </li>
            <li>
              <span className="font-medium text-fg">Can gravity-compensate.</span>{" "}
              Springs or a holding brake offset the arm’s own weight between lifts.
            </li>
            <li>
              <span className="font-medium text-fg">Does not violate physics.</span>{" "}
              Energy still comes from the battery. No free lift.
            </li>
          </ul>
        </aside>
      </div>
    </Section>
  );
}

function Cables() {
  return (
    <Section id="cables" kicker="03 — Drive" title="Motorcycle brake cables, powered.">
      <div className="grid gap-10 lg:grid-cols-2">
        <div className="space-y-5 text-base leading-relaxed text-muted">
          <p>
            Each line is a Bowden cable. The housing is a push-tube. The inner
            wire only pulls. The motor spool is the lever. The joint pulley is
            the caliper arm. Barrel adjusters live at the pack exit, ferrules
            seat on hard stops at the arm chassis, nipples lock into the sheave.
          </p>
          <p>
            Two cables at a joint are not duplicates. A wire cannot push. Cable A
            flexes. Cable B extends with control. That pair is biceps and triceps.
            Gravity can lower a load only while the motor pays cable out under
            tension — a crane, not a drop. Free-fall is a dumped spool. A usable
            exo never does that.
          </p>
        </div>
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full min-w-[28rem] text-left text-sm">
            <thead className="bg-elevated text-[11px] tracking-[0.18em] text-subtle uppercase">
              <tr>
                <th className="px-4 py-3 font-medium">Bike / moto</th>
                <th className="px-4 py-3 font-medium">CDX-3R</th>
              </tr>
            </thead>
            <tbody className="text-muted">
              {[
                ["Brake-lever nipple pocket", "Slot in the motor spool"],
                ["Barrel adjuster", "Threaded stop on the pack exit"],
                ["Spiral housing + ferrules", "Same housing, over the shoulder"],
                ["Housing stop on the frame", "Hard stop on the arm chassis"],
                ["Cable nipple at the caliper", "Nipple in the joint sheave"],
              ].map(([a, b]) => (
                <tr key={a} className="border-t border-border">
                  <td className="px-4 py-3">{a}</td>
                  <td className="px-4 py-3 text-fg">{b}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        <img
          src="/gallery/shoulder.jpg"
          alt="Shoulder pulley stack with dual Bowden cables"
          className="aspect-[3/2] w-full rounded-lg object-cover"
        />
        <img
          src="/gallery/elbow.jpg"
          alt="Elbow pulley with antagonist cables"
          className="aspect-[3/2] w-full rounded-lg object-cover"
        />
      </div>
    </Section>
  );
}

function Cad() {
  return (
    <Section id="cad" kicker="04 — Build" title="Arm through the cuffs. Sheave outside.">
      <p className="mb-8 max-w-2xl text-base leading-relaxed text-muted">
        The first CAD put the pulley in the elbow hole. That is not wearable.
        This is a brace: C-cuffs around the arm, hinge axis through the
        epicondyles, McMaster sheave on the <em>lateral</em> plate — outboard
        of the cuff wall. Nothing is bolted through flesh.
      </p>
      <p className="mb-8 max-w-2xl text-base leading-relaxed text-muted">
        Real hardware, one stack: 3434T121 sheave on a 91273A274 3/4 in
        shoulder screw, nylock on the inside of the plate. Two 608-2RS
        (6455K44) press into printed cups as cable fairleads. Same hole takes
        a 3434T157 ball-bearing sheave later — do not reprint.
      </p>
      <p className="mb-8 max-w-2xl text-base leading-relaxed text-muted">
        Cable path: dark Bowden runs <strong className="text-fg">up the upper arm to the shoulder / backpack</strong>.
        It stops in the green ferrules on the upper-arm plate — never down the
        forearm toward the wrist. Pink / violet inners exit, turn on the orange
        608s, wrap the gold sheave, and pinch on the pink clamps. The sheave
        is bolted to the forearm plate. The cuff is not a cable attachment.
      </p>
      <img
        src="/cad/elbow/preview/worn.png?v=4"
        alt="Wearable elbow: ghost arm through cuffs, sheave outboard on the lateral plate"
        className="mb-4 w-full rounded-lg border border-border"
      />
      <ul className="mb-8 flex flex-wrap gap-x-4 gap-y-2">
        {ELBOW_SWATCHES.map((s) => (
          <li key={s.id} className="flex items-center gap-2 font-mono text-[11px] tracking-[0.12em] text-muted uppercase">
            <span className="h-3 w-3 rounded-sm border border-border" style={{ background: s.hex }} />
            {s.label}
          </li>
        ))}
      </ul>
      <div className="mb-10 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {ELBOW_PREVIEWS.filter((p) => !p.title.startsWith("Worn")).map((p) => (
          <figure key={p.src} className="overflow-hidden rounded-lg border border-border bg-surface">
            <img src={p.src} alt={p.title} className="aspect-[3/2] w-full object-cover" />
            <figcaption className="px-3 py-2 font-mono text-[10px] tracking-[0.16em] text-subtle uppercase">
              {p.title}
            </figcaption>
          </figure>
        ))}
      </div>
      <details open className="mb-10 rounded-lg border border-border bg-surface p-4">
        <summary className="cursor-pointer font-mono text-xs tracking-[0.18em] text-muted uppercase">
          Orbit elbow in 3D — drag to rotate
        </summary>
        <div className="mt-4">
          <CadViewer kit="elbow" />
        </div>
      </details>
      <ol className="mb-10 grid gap-3 sm:grid-cols-5">
        {CAD_STAGES.map((s) => (
          <li key={s.n} className="rounded-lg border border-border bg-surface p-4">
            <div className="font-mono text-[10px] tracking-[0.22em] text-subtle uppercase">
              {s.n} · {s.status}
            </div>
            <div className="mt-1 font-display text-lg text-fg">{s.name}</div>
            <p className="mt-1 text-sm text-muted">{s.blurb}</p>
          </li>
        ))}
      </ol>

      <h3 className="font-display text-2xl tracking-wide text-fg">Human arm</h3>
      <p className="mt-2 mb-4 max-w-2xl text-sm text-muted">
        Adult male defaults. Measure the wearer and edit <code className="text-accent">cad/params.json</code>.
      </p>
      <div className="mb-10 grid gap-3 sm:grid-cols-3">
        {ELBOW_HUMAN.map((r) => (
          <div key={r.k} className="rounded-lg border border-border bg-surface p-4">
            <div className="font-mono text-[10px] tracking-[0.22em] text-subtle uppercase">{r.k}</div>
            <div className="mt-1 font-display text-xl text-fg">{r.v}</div>
            <p className="mt-1 text-sm text-muted">{r.d}</p>
          </div>
        ))}
      </div>

      <h3 className="font-display text-2xl tracking-wide text-fg">Physics at the elbow</h3>
      <div className="mb-10 mt-4 grid gap-3 lg:grid-cols-3">
        {ELBOW_PHYSICS.map((r) => (
          <div key={r.k} className="rounded-lg border border-border bg-surface p-4">
            <div className="font-mono text-[10px] tracking-[0.22em] text-subtle uppercase">{r.k}</div>
            <div className="mt-1 font-display text-xl text-fg">{r.v}</div>
            <p className="mt-1 text-sm text-muted">{r.d}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-10 lg:grid-cols-2">
        <div>
          <h3 className="font-display text-2xl tracking-wide text-fg">Buy</h3>
          <ul className="mt-4 divide-y divide-border border border-border rounded-lg">
            {ELBOW_BUY.map((p) => (
              <li key={p.item} className="flex gap-4 p-4">
                <span className="font-mono text-sm text-accent">{p.qty}</span>
                <span>
                  <a href={p.href} className="text-fg underline-offset-4 hover:underline">
                    {p.item}
                  </a>
                  <span className="mt-1 block text-sm text-muted">{p.why}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-display text-2xl tracking-wide text-fg">Print</h3>
          <ul className="mt-4 divide-y divide-border border border-border rounded-lg">
            {ELBOW_PRINT.map((p) => (
              <li key={p.file} className="flex flex-col gap-1 p-4 sm:flex-row sm:items-baseline sm:justify-between">
                <a href={`/cad/elbow/${p.file}`} download className="font-mono text-sm text-accent hover:underline">
                  {p.file}
                </a>
                <span className="text-sm text-muted">{p.note}</span>
              </li>
            ))}
          </ul>
          <a
            href="/cad/elbow/assembly_preview.stl"
            download
            className="mt-4 inline-block font-mono text-xs tracking-[0.18em] text-subtle uppercase hover:text-accent"
          >
            Preview assembly STL →
          </a>
        </div>
      </div>

      <h3 className="mt-16 font-display text-2xl tracking-wide text-fg">02 — Shoulder, two revolute</h3>
      <p className="mt-3 mb-8 max-w-2xl text-base leading-relaxed text-muted">
        Gold sheave is <strong className="text-fg">flexion</strong>, lateral,
        same idea as the elbow. Orange sheave is{" "}
        <strong className="text-fg">abduction</strong>, posterior, on the way
        to the pack. Cyan cables are the elbow pair — they pass the teal comb
        and do not wrap either shoulder sheave.
      </p>
      <img
        src="/cad/shoulder/preview/worn.png"
        alt="Shoulder 2R: flexion sheave lateral, abduction sheave posterior, elbow cables passing the comb"
        className="mb-4 w-full rounded-lg border border-border"
      />
      <details open className="mb-8 rounded-lg border border-border bg-surface p-4">
        <summary className="cursor-pointer font-mono text-xs tracking-[0.18em] text-muted uppercase">
          Orbit shoulder in 3D — drag to rotate
        </summary>
        <div className="mt-4">
          <CadViewer kit="shoulder" />
        </div>
      </details>
      <ul className="mb-8 flex flex-wrap gap-x-4 gap-y-2">
        {SHOULDER_SWATCHES.map((s) => (
          <li key={s.id} className="flex items-center gap-2 font-mono text-[11px] tracking-[0.12em] text-muted uppercase">
            <span className="h-3 w-3 rounded-sm border border-border" style={{ background: s.hex }} />
            {s.label}
          </li>
        ))}
      </ul>
      <div className="mb-10 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {SHOULDER_PREVIEWS.filter((p) => !p.title.startsWith("Worn")).map((p) => (
          <figure key={p.src} className="overflow-hidden rounded-lg border border-border bg-surface">
            <img src={p.src} alt={p.title} className="aspect-[3/2] w-full object-cover" />
            <figcaption className="px-3 py-2 font-mono text-[10px] tracking-[0.16em] text-subtle uppercase">
              {p.title}
            </figcaption>
          </figure>
        ))}
      </div>
      <div className="mb-10 grid gap-3 lg:grid-cols-4">
        {SHOULDER_PHYSICS.map((r) => (
          <div key={r.k} className="rounded-lg border border-border bg-surface p-4">
            <div className="font-mono text-[10px] tracking-[0.22em] text-subtle uppercase">{r.k}</div>
            <div className="mt-1 font-display text-xl text-fg">{r.v}</div>
            <p className="mt-1 text-sm text-muted">{r.d}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-10 lg:grid-cols-2">
        <div>
          <h3 className="font-display text-2xl tracking-wide text-fg">Buy (add to elbow kit)</h3>
          <ul className="mt-4 divide-y divide-border border border-border rounded-lg">
            {SHOULDER_BUY.map((p) => (
              <li key={p.item} className="flex gap-4 p-4">
                <span className="font-mono text-sm text-accent">{p.qty}</span>
                <span>
                  <a href={p.href} className="text-fg underline-offset-4 hover:underline">
                    {p.item}
                  </a>
                  <span className="mt-1 block text-sm text-muted">{p.why}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-display text-2xl tracking-wide text-fg">Print</h3>
          <ul className="mt-4 divide-y divide-border border border-border rounded-lg">
            {SHOULDER_PRINT.map((p) => (
              <li key={p.file} className="flex flex-col gap-1 p-4 sm:flex-row sm:items-baseline sm:justify-between">
                <a href={`/cad/shoulder/${p.file}`} download className="font-mono text-sm text-accent hover:underline">
                  {p.file}
                </a>
                <span className="text-sm text-muted">{p.note}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <h3 className="mt-16 font-display text-2xl tracking-wide text-fg">03 — Backpack, three winches</h3>
      <p className="mt-3 mb-8 max-w-2xl text-base leading-relaxed text-muted">
        Real motors and a real battery. 3× ODrive D6374 through 10:1
        planetaries onto printed drums. Hailong 48 V 13 Ah in a printed sled.
        3× S1 on a heat spreader. Six M5 barrel adjusters at the bulkhead —
        antagonist pair per axis. Housing stops here. Inners go to the drums.
      </p>
      <img
        src="/cad/backpack/preview/worn.png"
        alt="Backpack: Hailong battery, three D6374 winches, ODrive S1, cable bulkhead"
        className="mb-4 w-full rounded-lg border border-border"
      />
      <details open className="mb-8 rounded-lg border border-border bg-surface p-4">
        <summary className="cursor-pointer font-mono text-xs tracking-[0.18em] text-muted uppercase">
          Orbit backpack in 3D — drag to rotate
        </summary>
        <div className="mt-4">
          <CadViewer kit="backpack" />
        </div>
      </details>
      <ul className="mb-8 flex flex-wrap gap-x-4 gap-y-2">
        {PACK_SWATCHES.map((s) => (
          <li key={s.id} className="flex items-center gap-2 font-mono text-[11px] tracking-[0.12em] text-muted uppercase">
            <span className="h-3 w-3 rounded-sm border border-border" style={{ background: s.hex }} />
            {s.label}
          </li>
        ))}
      </ul>
      <div className="mb-10 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {PACK_PREVIEWS.filter((p) => !p.title.startsWith("Worn")).map((p) => (
          <figure key={p.src} className="overflow-hidden rounded-lg border border-border bg-surface">
            <img src={p.src} alt={p.title} className="aspect-[3/2] w-full object-cover" />
            <figcaption className="px-3 py-2 font-mono text-[10px] tracking-[0.16em] text-subtle uppercase">
              {p.title}
            </figcaption>
          </figure>
        ))}
      </div>
      <div className="mb-10 grid gap-3 lg:grid-cols-4">
        {PACK_PHYSICS.map((r) => (
          <div key={r.k} className="rounded-lg border border-border bg-surface p-4">
            <div className="font-mono text-[10px] tracking-[0.22em] text-subtle uppercase">{r.k}</div>
            <div className="mt-1 font-display text-xl text-fg">{r.v}</div>
            <p className="mt-1 text-sm text-muted">{r.d}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-10 lg:grid-cols-2">
        <div>
          <h3 className="font-display text-2xl tracking-wide text-fg">Buy</h3>
          <ul className="mt-4 divide-y divide-border border border-border rounded-lg">
            {PACK_BUY.map((p) => (
              <li key={p.item} className="flex gap-4 p-4">
                <span className="font-mono text-sm text-accent">{p.qty}</span>
                <span>
                  <a href={p.href} className="text-fg underline-offset-4 hover:underline">
                    {p.item}
                  </a>
                  <span className="mt-1 block text-sm text-muted">{p.why}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-display text-2xl tracking-wide text-fg">Print</h3>
          <ul className="mt-4 divide-y divide-border border border-border rounded-lg">
            {PACK_PRINT.map((p) => (
              <li key={p.file} className="flex flex-col gap-1 p-4 sm:flex-row sm:items-baseline sm:justify-between">
                <a href={`/cad/backpack/${p.file}`} download className="font-mono text-sm text-accent hover:underline">
                  {p.file}
                </a>
                <span className="text-sm text-muted">{p.note}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <h3 className="mt-16 font-display text-2xl tracking-wide text-fg">04 — One system, rest on the saddle</h3>
      <p className="mt-3 mb-8 max-w-2xl text-base leading-relaxed text-muted">
        Elbow + shoulder + pack as one structure. The exo{" "}
        <strong className="text-fg">sits on the amber saddle</strong> (trapezius /
        acromion). A yoke takes that load into the pack and hip belt. The
        red park rest holds the forearm in the rest pose. Cuffs couple torque.
        They do not hang 8 kg on your biceps.
      </p>
      <img
        src="/cad/system/preview/loadpath.png"
        alt="Load path: amber shoulder saddle, yoke to pack, hip belt, red park rest under the forearm"
        className="mb-4 w-full rounded-lg border border-border"
      />
      <img
        src="/cad/system/preview/worn.png"
        alt="Full CDX-3R system on a ghost wearer"
        className="mb-4 w-full rounded-lg border border-border"
      />
      <details open className="mb-8 rounded-lg border border-border bg-surface p-4">
        <summary className="cursor-pointer font-mono text-xs tracking-[0.18em] text-muted uppercase">
          Orbit full system in 3D — drag to rotate
        </summary>
        <div className="mt-4">
          <CadViewer kit="system" />
        </div>
      </details>
      <ul className="mb-8 flex flex-wrap gap-x-4 gap-y-2">
        {SYSTEM_SWATCHES.map((s) => (
          <li key={s.id} className="flex items-center gap-2 font-mono text-[11px] tracking-[0.12em] text-muted uppercase">
            <span className="h-3 w-3 rounded-sm border border-border" style={{ background: s.hex }} />
            {s.label}
          </li>
        ))}
      </ul>
      <div className="mb-10 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {SYSTEM_PREVIEWS.filter((p) => !p.title.startsWith("Worn") && !p.title.startsWith("Load")).map((p) => (
          <figure key={p.src} className="overflow-hidden rounded-lg border border-border bg-surface">
            <img src={p.src} alt={p.title} className="aspect-[3/2] w-full object-cover" />
            <figcaption className="px-3 py-2 font-mono text-[10px] tracking-[0.16em] text-subtle uppercase">
              {p.title}
            </figcaption>
          </figure>
        ))}
      </div>
      <div className="mb-10 grid gap-3 lg:grid-cols-4">
        {SYSTEM_PHYSICS.map((r) => (
          <div key={r.k} className="rounded-lg border border-border bg-surface p-4">
            <div className="font-mono text-[10px] tracking-[0.22em] text-subtle uppercase">{r.k}</div>
            <div className="mt-1 font-display text-xl text-fg">{r.v}</div>
            <p className="mt-1 text-sm text-muted">{r.d}</p>
          </div>
        ))}
      </div>
      <div>
        <h3 className="font-display text-2xl tracking-wide text-fg">Print (load path)</h3>
        <ul className="mt-4 divide-y divide-border border border-border rounded-lg">
          {SYSTEM_PRINT.map((p) => (
            <li key={p.file} className="flex flex-col gap-1 p-4 sm:flex-row sm:items-baseline sm:justify-between">
              <a href={`/cad/system/${p.file}`} download className="font-mono text-sm text-accent hover:underline">
                {p.file}
              </a>
              <span className="text-sm text-muted">{p.note}</span>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

function Motion() {
  const featured = MOTION.find((c) => c.featured) ?? MOTION[0];
  const rest = MOTION.filter((c) => c !== featured);

  return (
    <Section id="motion" kicker="05 — Motion" title="Watch the two lift joints, not a 7-axis wrist.">
      <p className="mb-8 max-w-2xl text-base leading-relaxed text-muted">
        CDX-3R only powers shoulder flexion and elbow flexion for this lift.
        Abduction is the third axis (clear the hip). Wrist plating is dummy —
        it does not articulate.
      </p>
      <Clip clip={featured} className="mb-6" large />
      <div className="grid gap-6 lg:grid-cols-3">
        {rest.map((clip) => (
          <Clip key={clip.src} clip={clip} />
        ))}
      </div>
    </Section>
  );
}

function Clip({
  clip,
  className,
  large,
}: {
  clip: (typeof MOTION)[number];
  className?: string;
  large?: boolean;
}) {
  return (
    <article className={cn("overflow-hidden rounded-lg border border-border bg-surface", className)}>
      <video
        className={cn("w-full bg-elevated object-cover", large ? "aspect-video" : "aspect-video")}
        poster={clip.poster}
        autoPlay
        muted
        loop
        playsInline
        controls
        preload="metadata"
      >
        <source src={clip.src} type="video/mp4" />
      </video>
      <div className="p-4">
        <h3 className="font-display text-lg tracking-wide text-fg">{clip.title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-muted">{clip.caption}</p>
      </div>
    </article>
  );
}

function Safety() {
  return (
    <Section id="safety" kicker="06 — Safety" title="Power off must still let you move.">
      <div className="grid gap-6 lg:grid-cols-3">
        {[
          {
            n: "Free",
            d: "Motors off, clutch open, brake released. Cables slack or pulleys freewheel. The suit is extra mass and friction. You can walk, don, and dump the pack.",
          },
          {
            n: "Hold",
            d: "Crate stays put with little motor power. Disc brake or non-backdrivable gear on the spool — not a lock pin in the joint. Pins are binary. Arms need creep.",
          },
          {
            n: "Assist",
            d: "Sensors read intent. Motors add torque a few milliseconds later. If the crate swings, the second shoulder axis fires so the frame stays aligned.",
          },
        ].map((s) => (
          <article key={s.n} className="rounded-lg border border-border bg-surface p-6">
            <div className="font-mono text-[11px] tracking-[0.22em] text-accent uppercase">Mode</div>
            <h3 className="mt-2 font-display text-2xl tracking-wide text-fg">{s.n}</h3>
            <p className="mt-3 text-sm leading-relaxed text-muted">{s.d}</p>
          </article>
        ))}
      </div>
      <div className="mt-10 grid items-center gap-8 lg:grid-cols-2">
        <img
          src="/gallery/release.jpg"
          alt="Red T-handle emergency release on the right shoulder plate"
          className="aspect-[3/2] w-full rounded-xl object-cover"
        />
        <div className="space-y-4 text-base leading-relaxed text-muted">
          <h3 className="font-display text-2xl tracking-wide text-fg">Left hand, right collarbone.</h3>
          <p>
            Brakes and clutches stay in the pack. The thing you slap is a lever.
            Best spot: front of the right shoulder plate — same motion as ripping
            a radio mic. Big, red, no hunting for a pin. Duplicate on the chest
            buckle if armor buries the shoulder.
          </p>
          <p>
            Yank opens clutch and dumps the brake. Optional parking pawl is on
            the spool, never a pin through the glenohumeral joint. You need to
            live in this arm.
          </p>
        </div>
      </div>
    </Section>
  );
}

function Gallery() {
  const [open, setOpen] = useState<number | null>(null);
  const shot = open !== null ? GALLERY[open] : null;

  return (
    <Section id="gallery" kicker="07 — Gallery" title="The machine, not the warehouse uniform.">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {GALLERY.map((g, i) => (
          <button
            key={g.src}
            type="button"
            onClick={() => setOpen(i)}
            className="group overflow-hidden rounded-lg border border-border bg-surface text-left"
          >
            <img
              src={g.src}
              alt={g.title}
              className="aspect-[3/2] w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            />
            <div className="p-4">
              <div className="font-display text-lg tracking-wide text-fg">{g.title}</div>
              <p className="mt-1 text-sm text-muted">{g.caption}</p>
            </div>
          </button>
        ))}
      </div>
      {shot && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-bg/85 p-4"
          onClick={() => setOpen(null)}
          role="dialog"
          aria-modal="true"
          aria-label={shot.title}
        >
          <div
            className="relative max-h-[90vh] w-full max-w-5xl overflow-hidden rounded-xl border border-border bg-surface"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setOpen(null)}
              className="absolute top-3 right-3 z-10 flex size-11 items-center justify-center rounded-sm bg-bg/80 text-fg"
              aria-label="Close"
            >
              <X className="size-5" />
            </button>
            <img src={shot.src} alt={shot.title} className="max-h-[78vh] w-full object-contain" />
            <div className="px-5 py-4">
              <div className="font-display text-xl text-fg">{shot.title}</div>
              <p className="mt-1 text-sm text-muted">{shot.caption}</p>
            </div>
          </div>
        </div>
      )}
    </Section>
  );
}

function Cost() {
  const [id, setId] = useState<(typeof COST_TIERS)[number]["id"]>("serious");
  const tier = COST_TIERS.find((t) => t.id === id) ?? COST_TIERS[1];

  return (
    <Section id="cost" kicker="08 — Cost" title="Money is in machining, not the cables.">
      <div className="flex flex-wrap gap-2">
        {COST_TIERS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setId(t.id)}
            className={cn(
              "min-h-11 rounded-sm border px-4 text-sm font-medium transition-colors duration-150",
              t.id === id
                ? "border-fg bg-fg text-bg"
                : "border-border bg-transparent text-muted hover:text-fg",
            )}
          >
            {t.name}
          </button>
        ))}
      </div>
      <div className="mt-8 rounded-xl border border-border bg-surface p-6 sm:p-8">
        <div className="font-display text-4xl tracking-tight text-fg">{tier.range}</div>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-muted">{tier.blurb}</p>
        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="font-mono text-[10px] tracking-[0.2em] text-subtle uppercase">Parts</dt>
            <dd className="mt-1 text-fg">{tier.parts}</dd>
          </div>
          <div>
            <dt className="font-mono text-[10px] tracking-[0.2em] text-subtle uppercase">Fab + labor</dt>
            <dd className="mt-1 text-fg">{tier.labor}</dd>
          </div>
        </dl>
      </div>
      <h3 className="mt-12 font-display text-2xl tracking-wide text-fg">Parts, serious one-off</h3>
      <div className="mt-4 overflow-x-auto rounded-xl border border-border">
        <table className="w-full min-w-[32rem] text-left text-sm">
          <thead className="bg-elevated text-[11px] tracking-[0.18em] text-subtle uppercase">
            <tr>
              <th className="px-4 py-3 font-medium">Bucket</th>
              <th className="px-4 py-3 font-medium">Low</th>
              <th className="px-4 py-3 font-medium">High</th>
            </tr>
          </thead>
          <tbody>
            {BOM.map((row) => (
              <tr key={row.item} className="border-t border-border">
                <td className="px-4 py-3 text-fg">{row.item}</td>
                <td className="px-4 py-3 font-mono text-muted">{row.low}</td>
                <td className="px-4 py-3 font-mono text-muted">{row.high}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}

function Sponsor() {
  return (
    <Section id="sponsor" kicker="09 — Raise" title="The prop gets the meeting. The bench gets the check.">
      <p className="max-w-2xl text-base leading-relaxed text-muted">
        Sponsors fund a path, not a pretty still. Do not tell anyone it lifts
        30 kg if it does not. Pitch: this is the industrial-design target. Here
        is a working cable module. Fund wearable integration.
      </p>
      <div className="mt-8 overflow-x-auto rounded-xl border border-border">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <thead className="bg-elevated text-[11px] tracking-[0.18em] text-subtle uppercase">
            <tr>
              <th className="px-4 py-3 font-medium">Piece</th>
              <th className="px-4 py-3 font-medium">Real or fake</th>
              <th className="px-4 py-3 font-medium">Why</th>
            </tr>
          </thead>
          <tbody>
            {SPONSOR_SPLIT.map((row) => (
              <tr key={row.piece} className="border-t border-border">
                <td className="px-4 py-3 text-fg">{row.piece}</td>
                <td className="px-4 py-3 text-muted">{row.real}</td>
                <td className="px-4 py-3 text-muted">{row.why}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {[
          ["Worn look-alike", "$2k–$5k", "Hero-prop finish. Hard armor, dummy motor faces, real cable cosmetics."],
          ["Live bench module", "+$800–$2k", "One motor, driver, spool, brake, load cell. Film it pulling a known weight."],
          ["Ask", "$25k–$40k", "Reach a limited 15–20 kg wearable prototype and test fixtures."],
        ].map(([t, n, d]) => (
          <article key={t} className="rounded-lg border border-border bg-surface p-6">
            <div className="font-mono text-[10px] tracking-[0.2em] text-subtle uppercase">{t}</div>
            <div className="mt-2 font-display text-3xl tracking-tight text-fg">{n}</div>
            <p className="mt-3 text-sm leading-relaxed text-muted">{d}</p>
          </article>
        ))}
      </div>
      <div className="mt-10 overflow-hidden rounded-xl">
        <img
          src="/gallery/winch.jpg"
          alt="Instrumented winch module on a workbench"
          className="aspect-[4/3] w-full object-cover sm:aspect-[21/9]"
        />
      </div>
      <p className="mt-4 text-sm text-subtle">
        Three honest claims only: the exterior is the target look; one module
        produces measurable torque on the bench; a worn 15–20 kg unit is the
        funded next step — not a delivered product.
      </p>
    </Section>
  );
}
