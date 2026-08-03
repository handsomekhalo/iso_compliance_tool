'use client';

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
// import { mockRegister } from "@/lib/mock-data";
import {AuthShell}  from "../../../../AuthShell";
import  {useAuth}  from '../../../../AuthContext';


export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    bankName: "",
    contactEmail: "",
    adminEmail: "",
    password: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    if (!form.bankName || !form.contactEmail || !form.adminEmail || !form.password) {
      setError("All fields are required to open an institution account.");
      return;
    }
    if (form.password.length < 8) {
      setError("Administrator password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    // Mock only — replace with a real call to backendApi during integration
    const res = await mockRegister(form.bankName, form.adminEmail);
    login(res);
    router.replace("/dashboard?firstRun=true");
  }

  return (
    <AuthShell
      title="Register your institution"
      subtitle="Create your bank profile and the first administrator account."
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="bank">Registered bank name</Label>
          <Input
            id="bank"
            placeholder="e.g. Rand Merchant Bank"
            value={form.bankName}
            onChange={set("bankName")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="contact">Compliance contact email</Label>
          <Input
            id="contact"
            type="email"
            placeholder="compliance@bank.co.za"
            value={form.contactEmail}
            onChange={set("contactEmail")}
          />
        </div>
        <div className="h-px bg-border" />
        <div className="space-y-2">
          <Label htmlFor="adminEmail">Administrator email</Label>
          <Input
            id="adminEmail"
            type="email"
            placeholder="admin@bank.co.za"
            value={form.adminEmail}
            onChange={set("adminEmail")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="pw">Administrator password</Label>
          <Input id="pw" type="password" value={form.password} onChange={set("password")} />
        </div>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
          {submitting ? "Creating institution" : "Create institution account"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted-foreground">
        Already onboarded?{" "}
        <Link href="/login" className="font-medium text-primary underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}