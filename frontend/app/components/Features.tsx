export default function Features() {
  const features = [
    {
      title: "Soil Monitoring",
      description:
        "Track soil moisture levels across all your fields in real time with sensor-driven data.",
      icon: "💧",
    },
    {
      title: "Weather Integration",
      description:
        "Automatic weather data collection including rainfall, temperature, humidity, and evapotranspiration.",
      icon: "🌤",
    },
    {
      title: "Stress Predictions",
      description:
        "ML-powered forecasts that tell you when water stress is coming days before it happens.",
      icon: "📊",
    },
    {
      title: "Smart Alerts",
      description:
        "Get notified when your fields need attention so you never miss a critical irrigation window.",
      icon: "🔔",
    },
  ];

  return (
    <section className="bg-zinc-950 py-24 px-8">
      <div className="max-w-7xl mx-auto">
        <p className="text-amber-400 text-sm font-semibold tracking-widest uppercase mb-4">
          What We Offer
        </p>
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-16 max-w-2xl">
          Everything you need to stay ahead of water stress
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
            >
              <span className="text-3xl">{feature.icon}</span>
              <h3 className="text-white font-semibold text-lg mt-4 mb-2">
                {feature.title}
              </h3>
              <p className="text-white/60 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
