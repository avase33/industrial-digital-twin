import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "idt · digital twin",
  description: "Industrial IoT digital twin — Go hub · Rust point-cloud · Python GNN · Three.js.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
