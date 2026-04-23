"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAuth } from "@/lib/auth";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const auth = getAuth();
    router.replace(auth ? "/chat" : "/login");
  }, [router]);
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
      <div style={{ color: "var(--text-secondary)", fontSize: 14 }}>Đang tải...</div>
    </div>
  );
}
