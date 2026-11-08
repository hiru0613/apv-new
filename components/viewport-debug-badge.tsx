"use client";

import { useEffect, useState } from "react";

/**
 * 临时诊断：底部露白时在屏幕最下方打一行读数。
 * 只在“外壳底边没贴住视口”或“页面被系统偏移”时显示，平时不占地方。
 * 定位到真因后整个文件删掉。
 */
export function ViewportDebugBadge() {
  const [info, setInfo] = useState("");

  useEffect(() => {
    const tick = () => {
      const vv = window.visualViewport;
      const shell = document.querySelector<HTMLElement>(".phone-shell-wrap");
      const rect = shell?.getBoundingClientRect();
      const gap = rect ? Math.round(window.innerHeight - rect.bottom) : -1;
      const offsetTop = Math.round(vv?.offsetTop ?? 0);
      const scrollY = Math.round(window.scrollY);
      const forced = window.location.hash === "#vp";
      const bad = forced || offsetTop !== 0 || scrollY !== 0 || gap > 2;
      if (!bad) {
        setInfo("");
        return;
      }
      const cs = shell ? getComputedStyle(shell) : null;
      const drop = cs?.getPropertyValue("--status-bar-drop").trim() || "0";
      const lift = cs?.getPropertyValue("--mobile-keyboard-lift").trim() || "0";
      setInfo(
        `ih=${window.innerHeight} vv=${Math.round(vv?.height ?? 0)} top=${offsetTop} sy=${scrollY}`
        + ` de=${document.documentElement.clientHeight} sh=${Math.round(rect?.height ?? 0)}`
        + ` gap=${gap} dpr=${Math.round(window.devicePixelRatio * 100) / 100}`
        + ` drop=${drop} lift=${lift}`,
      );
    };

    tick();
    const id = window.setInterval(tick, 600);
    window.addEventListener("resize", tick);
    window.addEventListener("orientationchange", tick);
    window.visualViewport?.addEventListener("resize", tick);
    window.visualViewport?.addEventListener("scroll", tick);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("resize", tick);
      window.removeEventListener("orientationchange", tick);
      window.visualViewport?.removeEventListener("resize", tick);
      window.visualViewport?.removeEventListener("scroll", tick);
    };
  }, []);

  if (!info) return null;
  return (
    <div
      style={{
        position: "fixed",
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 2147483647,
        background: "rgba(0,0,0,0.85)",
        color: "#8ef",
        font: "10px/1.5 ui-monospace, SFMono-Regular, monospace",
        padding: "2px 6px",
        pointerEvents: "none",
        whiteSpace: "normal",
      }}
    >
      {info}
    </div>
  );
}
