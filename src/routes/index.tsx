import { createFileRoute } from "@tanstack/react-router";
import { useState, type ReactNode } from "react";
import { SiteNav } from "@/components/cdx/nav";
import { Button } from "@/components/ui/button";
import {
  BOM,
  COST_TIERS,
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

function Motion() {
  return (
    <Section id="motion" kicker="04 — Motion" title="Three revolute axes. That is the whole machine.">
      <p className="mb-8 max-w-2xl text-base leading-relaxed text-muted">
        7R would be a robot arm: three shoulder, one elbow, three wrist. CDX-3R
        only powers the lift. Wrist plating is passive so the hand can still
        square on the crate.
      </p>
      <div className="grid gap-6 lg:grid-cols-3">
        {MOTION.map((clip) => (
          <article key={clip.src} className="overflow-hidden rounded-lg border border-border bg-surface">
            <video
              className="aspect-video w-full bg-elevated object-cover"
              src={clip.src}
              poster={clip.poster}
              autoPlay
              muted
              loop
              playsInline
              controls
            />
            <div className="p-4">
              <h3 className="font-display text-lg tracking-wide text-fg">{clip.title}</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted">{clip.caption}</p>
            </div>
          </article>
        ))}
      </div>
    </Section>
  );
}

function Safety() {
  return (
    <Section id="safety" kicker="05 — Safety" title="Power off must still let you move.">
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
    <Section id="gallery" kicker="06 — Gallery" title="The machine, not the warehouse uniform.">
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
    <Section id="cost" kicker="07 — Cost" title="Money is in machining, not the cables.">
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
    <Section id="sponsor" kicker="08 — Raise" title="The prop gets the meeting. The bench gets the check.">
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
