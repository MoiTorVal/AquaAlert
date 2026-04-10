"use client";

import { useState } from "react";
import Input from "../components/Input";
import Image from "next/image";

interface FormFields {
  name: string;
  email: string;
  subject: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  subject?: string;
  message?: string;
}

function validate(fields: FormFields): FormErrors {
  const errors: FormErrors = {};
  if (!fields.name.trim()) errors.name = "Name is required";
  if (!fields.email.trim()) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email)) {
    errors.email = "Invalid email format";
  }
  if (!fields.subject.trim()) errors.subject = "Subject is required";
  if (!fields.message.trim()) errors.message = "Message is required";
  return errors;
}

export default function ContactPage() {
  const [fields, setFields] = useState<FormFields>({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) {
    setFields((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setErrors((prev) => ({ ...prev, [e.target.name]: undefined }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const validationErrors = validate(fields);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setLoading(false);
    setSubmitted(true);
  }

  return (
    <main className="min-h-screen bg-bg-primary pt-32 pb-24 px-8">
      <div className="max-w-7xl mx-auto">
        <p className="text-muted text-sm font-medium tracking-widest uppercase mb-4">
          Get In Touch
        </p>
        <h1 className="text-4xl md:text-5xl font-semibold text-surface mb-16 max-w-xl">
          We&apos;d love to hear from you
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
          {/* Left — image */}
          <div className="rounded-2xl overflow-hidden bg-white/5 aspect-[4/3] relative">
            <Image
              src="/images/contact.png"
              alt="Irrigated crop field at sunrise"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 50vw"
              priority
            />
          </div>

          {/* Right — form */}
          {submitted ? (
            <div className="flex flex-col justify-center h-full gap-4">
              <h2 className="text-2xl font-semibold text-surface">
                Message sent!
              </h2>
              <p className="text-muted">
                Thanks for reaching out. We&apos;ll get back to you shortly.
              </p>
            </div>
          ) : (
            <form
              onSubmit={handleSubmit}
              noValidate
              className="flex flex-col gap-6"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <Input
                  label="Name"
                  name="name"
                  value={fields.name}
                  onChange={handleChange}
                  placeholder="John Smith"
                  error={errors.name}
                />
                <Input
                  label="Email"
                  name="email"
                  type="email"
                  value={fields.email}
                  onChange={handleChange}
                  placeholder="john@example.com"
                  error={errors.email}
                />
              </div>

              <Input
                label="Subject"
                name="subject"
                value={fields.subject}
                onChange={handleChange}
                placeholder="What's this about?"
                error={errors.subject}
              />

              <Input
                label="Message"
                name="message"
                value={fields.message}
                onChange={handleChange}
                placeholder="Your message..."
                error={errors.message}
                multiline
                rows={5}
              />

              <button
                type="submit"
                disabled={loading}
                className="bg-btn-secondary hover:bg-white disabled:opacity-50 text-btn-text font-semibold px-8
py-3 rounded-lg transition-colors w-fit"
              >
                {loading ? "Sending..." : "Send Message"}
              </button>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
