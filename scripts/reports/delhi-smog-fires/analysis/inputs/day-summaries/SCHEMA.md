# HamariHawa day summaries (input to the NOAA-20 cross-check)

Fetched 2026-11-09 from `https://hamarihawa.org/api/day?d=YYYY-MM-DD` (schema `v: 2`), 1 October-10 November of 2019-2026.

`summary.states["IN|Punjab"]` is `[spots from all satellites, ..., snpp, ...]`. Index 2 is the single-satellite count used here.

The key is called `snpp` for historical reasons. It counted Suomi NPP until NASA stopped delivering that satellite's data, and the archive was
rebuilt on NOAA-20 on 2 November 2026. Since then `snpp` counts only what NOAA-20 saw (documented at https://hamarihawa.org/data/, read 11 Nov 2026).
These files were fetched after the rebuild, so the cross-check is a NOAA-20 series. Counts are fire spots (merged detections), not detections.
