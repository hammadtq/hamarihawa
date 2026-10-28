// The URL of a live link-preview image (scripts/build-og-live.py redraws them every 3 hours). The ?v= changes
// with each 3-hour slot, because WhatsApp, Facebook and X cache previews by image URL.
// OG_REV changes when the cards' design does, so previews already cached are fetched again.
export const OG_REV = "d";
export const ogSlot = () => `${Math.floor(Date.now() / 10800000)}${OG_REV}`;
export const ogUrl = (id) => `https://hamarihawa.org/og/live/${id}.jpg?v=${ogSlot()}`;
