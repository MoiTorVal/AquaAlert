"use client";

import dynamic from "next/dynamic";

const DemoFieldNdviMap = dynamic(() => import("./DemoFieldNdviMap"), {
  ssr: false,
  loading: () => <div className="h-72 animate-pulse rounded-xl bg-gray-100" />,
});

export default DemoFieldNdviMap;
