// Farmers trace boundaries off what their field actually looks like, so both
// map components use satellite imagery with a place-label reference layer on
// top (plain imagery has no town names to navigate by).
export const IMAGERY_URL =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

export const IMAGERY_ATTRIBUTION =
  'Imagery &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Source: Esri, Maxar, Earthstar Geographics, USDA, USGS';

export const LABELS_URL =
  "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}";
