"use client";
import { useEffect, useState } from "react";
export function ViewportDebugBadge() {
  const [info, setInfo] = useState("");
  useEffect(() => {
    const tick = () => {
      const vv = window.visualViewport;
      const de = document.documentElement;
      const root = document.querySelector<HTMLElement>(".app-root");
      const shell = document.querySelector<HTMLElement>(".phone-shell-wrap");
      const bar = document.querySelector<HTMLElement>(".chat-input-bar");
      const r = shell ? shell.getBoundingClientRect() : null;
      const rr = root ? root.getBoundingClientRect() : null;
      const br = bar ? bar.getBoundingClientRect() : null;
      setInfo(
        `p=${location.pathname} ih=${window.innerHeight} vv=${Math.round(vv?.height ?? 0)}/${Math.round(vv?.offsetTop ?? 0)}`
        + ` sy=${Math.round(window.scrollY)} de=${de.clientHeight} dh=${de.scrollHeight}`
        + ` root=${Math.round(rr?.height ?? 0)}@${Math.round(rr?.top ?? 0)}`
        + ` shell=${Math.round(r?.height ?? 0)}@${Math.round(r?.top ?? 0)}`
        + ` bar=${Math.round(br?.bottom ?? 0)}`
        + ` gap=${Math.round(window.innerHeight - (r?.bottom ?? 0))}`
      );
    };
    tick();
    const id = window.setInterval(tick, 500);
    window.addEventListener("resize", tick);
    window.visualViewport?.addEventListener("resize", tick);
    window.visualViewport?.addEventListener("scroll", tick);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("resize", tick);
      window.visualViewport?.removeEventListener("resize", tick);
      window.visualViewport?.removeEventListener("scroll", tick);
    };
  }, []);
  return (
    <div style={{ position: "fixed", left: 0, right: 0, bottom: 0, zIndex: 2147483647, background: "rgba(0,0,0,0.9)", color: "#7ff", font: "9px/1.4 ui-monospace, monospace", padding: "2px 4px", pointerEvents: "none" }}>
      {info}
    </div>
  );
}
