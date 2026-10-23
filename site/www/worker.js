// www.hamarihawa.org -> hamarihawa.org, keeping the path and query. Its own Worker because the main one
// no longer runs for static files, so it can't redirect them.
export default {
  fetch(request) {
    const url = new URL(request.url);
    url.protocol = "https:";
    url.hostname = "hamarihawa.org";
    return Response.redirect(url.toString(), 301);
  },
};
