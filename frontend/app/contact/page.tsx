"use client";

import { useState } from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

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
    setFields((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
    setErrors((prev) => ({
      ...prev,
      [e.target.name]: undefined,
    }));
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
    <>
      <Navbar />
      <main className="min-h-screen bg-zinc-900 pt-32 pb-24 px-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-amber-400 text-sm font-semibold tracking-widest uppercase mb-4">
            Get In Touch
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-16 max-w-xl">
            We'd love to hear from you
          </h1>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
            {/* Left — image */}
            <div className="rounded-2xl overflow-hidden bg-zinc-800 aspect-[4/3]">
              <img
                src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8ZmFybWVyJTIwaW4lMjBmaWVsZHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
                alt="Farmer in field"
                className="w-full h-full object-cover opacity-80"
              />
            </div>

            {/* Right — form */}
            {submitted ? (
              <div className="flex flex-col justify-center h-full gap-4">
                <h2 className="text-2xl font-bold text-white">Message sent!</h2>
                <p className="text-white/60">
                  Thanks for reaching out. We'll get back to you shortly.
                </p>
              </div>
            ) : (
              <form
                onSubmit={handleSubmit}
                noValidate
                className="flex flex-col gap-6"
              >
                {/* Name + Email */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="flex flex-col gap-1">
                    <label className="text-white/70 text-sm font-medium">
                      Name
                    </label>
                    <input
                      name="name"
                      value={fields.name}
                      onChange={handleChange}
                      placeholder="John Smith"
                      className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white              
  placeholder:text-zinc-500 focus:outline-none focus:border-amber-500"
                    />
                    {errors.name && (
                      <p className="text-red-400 text-xs">{errors.name}</p>
                    )}
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-white/70 text-sm font-medium">
                    Email
                  </label>
                  <input
                    name="email"
                    value={fields.email}
                    onChange={handleChange}
                    placeholder="john@example.com"
                    className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white
 placeholder:text-zinc-500 focus:outline-none focus:border-amber-500"
                  />
                  {errors.email && (
                    <p className="text-red-400 text-xs">{errors.email}</p>
                  )}
                </div>

                {/* Subject */}
                <div className="flex flex-col gap-1">
                  <label className="text-white/70 text-sm font-medium">
                    Subject
                  </label>
                  <input
                    name="subject"
                    value={fields.subject}
                    onChange={handleChange}
                    placeholder="What's this about?"
                    className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white
  placeholder:text-zinc-500 focus:outline-none focus:border-amber-500"
                  />
                  {errors.subject && (
                    <p className="text-red-400 text-xs">{errors.subject}</p>
                  )}
                </div>

                {/* Message */}
                <div className="flex flex-col gap-1">
                  <label className="text-white/70 text-sm font-medium">
                    Message
                  </label>
                  <textarea
                    name="message"
                    value={fields.message}
                    onChange={handleChange}
                    placeholder="Your message..."
                    rows={5}
                    className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white
  placeholder:text-zinc-500 focus:outline-none focus:border-amber-500 resize-none"
                  />
                  {errors.message && (
                    <p className="text-red-400 text-xs">{errors.message}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-zinc-900 font-semibold px-8
   py-3 rounded-full transition-colors w-fit"
                >
                  {loading ? "Sending..." : "Send Message"}
                </button>
              </form>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
