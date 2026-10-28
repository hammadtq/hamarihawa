// The URL of a live link-preview image (scripts/build-og-live.py redraws them every 3 hours). The ?v= changes
// with each 3-hour slot, because WhatsApp, Facebook and X cache previews by image URL.
export const ogUrl = (id) => `https://hamarihawa.org/og/live/${id}.jpg?v=${Math.floor(Date.now() / 10800000)}`;
