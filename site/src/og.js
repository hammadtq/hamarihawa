// The URL of a live link-preview image (scripts/build-og-live.py redraws them every hour). The ?v= changes
// with each hour, because WhatsApp, Facebook and X cache previews by image URL.
// OG_REV changes when the cards' design does, so previews already cached are fetched again.
export const OG_REV = "e";
export const ogSlot = () => `${Math.floor(Date.now() / 3600000)}${OG_REV}`;
export const ogUrl = (id) => `https://hamarihawa.org/og/live/${id}.jpg?v=${ogSlot()}`;
