"use client";

import React, { useEffect, useState } from "react";
import PanzarActivityFeed from "./PanzarActivityFeed";

export default function Page() {
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Example: fetch data
  useEffect(() => {
    async function load() {
      try {
        // Replace with your API call
        const res = await fetch("/api/panzar/activity");
        const data = await res.json();
        setActivities(data || []);
      } catch (e) {
        setActivities([]);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="p-6">
      <PanzarActivityFeed activities={activities} isLoading={isLoading} />
    </div>
  );
}
