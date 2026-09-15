import { NAV } from "@/lib/cdx";

export function SiteNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3 sm:px-6">
        <a href="#top" className="shrink-0 font-display text-lg tracking-[0.18em] text-fg">
          CDX-3R
        </a>
        <nav className="-mx-1 flex min-w-0 flex-1 gap-1 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {NAV.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="shrink-0 rounded-sm px-3 py-2 text-xs font-medium tracking-wide text-muted uppercase transition-colors duration-150 hover:text-fg"
            >
              {item.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
