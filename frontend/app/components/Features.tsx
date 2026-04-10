import { LucideIcon, Droplets, Cloud, TrendingUp, Bell } from "lucide-react";

export default function Features() {
  const features: { title: string; description: string; icon: LucideIcon }[] = [
    {
      title: "Soil Monitoring",
      description:
        "Track soil moisture levels across all your fields in real time with sensor-driven data.",
      icon: Droplets,
    },
    {
      title: "Weather Integration",
      description:
        "Automatic weather data collection including rainfall, temperature, humidity, and evapotranspiration.",
      icon: Cloud,
    },
    {
      title: "Stress Predictions",
      description:
        "ML-powered forecasts that tell you when water stress is coming days before it happens.",
      icon: TrendingUp,
    },
    {
      title: "Smart Alerts",
      description:
        "Get notified when your fields need attention so you never miss a critical irrigation window.",
      icon: Bell,
    },
  ];

  return (
    <section className="bg-bg-primary py-24 px-8 border-t border-white/10">
      <div className="max-w-7xl mx-auto">
        <p className="text-muted text-sm font-medium tracking-widest uppercase mb-4">
          What We Offer
        </p>
        <h2 className="text-3xl md:text-4xl font-semibold text-surface mb-16 max-w-2xl">
          Everything you need to stay ahead of water stress
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/[0.07] transition-colors"
            >
              <feature.icon size={24} className="text-surface" />
              <h3 className="text-surface font-semibold text-base mt-4 mb-2">
                {feature.title}
              </h3>
              <p className="text-muted text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
