// My JavaScript skills are like shit, but works perfectly for a dev-environment-only feature.

console.log("LivePreview | AmiaBlog LivePreviewLib loaded")

const WS_URL = (document.location.protocol == "http:" ? "ws" : "wss") + "://" + document.location.host + "/api/live-preview-ws"
const ws = new WebSocket(WS_URL)

ws.onopen = () => {
  console.log("LivePreview | WebSocket connected")
  ws.send(JSON.stringify(
    {
      type: "subscribe",
      slug: window._amiablog_slug
    }
  ))
}

ws.onmessage = (evt) => {
  const data = JSON.parse(evt.data)
  switch(data.type) {
    case "update":
      console.log("LivePreview | Received update package", data)
      mdui.$('#post-content')[0].innerHTML = data.markdown
      window._amiablog_renderPage()
      break
    case "refresh":
      console.log("LivePreview | Refresh requested")
      document.location.reload()
      break
    case "success":
      console.log("LivePreview | Subscribe Succeed", data)
      break
    case "error":
      console.log("LivePreview | Subscribe Failed", data)
      mdui.alert({
        headline: window._amiablog_i18n_ctx.live_preview_subscribe_failed,
        description: data.message
      })
      break
    case "pong":
      console.log("LivePreview | Heartbeat", data)
      break
  }
}

ws.onclose = () => {
  console.log("LivePreview WebSocket disconnected")
  mdui.alert({
    headline: window._amiablog_i18n_ctx.live_preview_connection_failed,
    description: window._amiablog_i18n_ctx.live_preview_connection_failed_desc
  })
}

ws.onerror = (evt) => {
  console.log("LivePreview WebSocket error", evt)
  mdui.alert({
    headline: window._amiablog_i18n_ctx.live_preview_connection_failed,
    description: window._amiablog_i18n_ctx.live_preview_connection_failed_desc
  })
}

setInterval(() => {
  if(ws.readyState == WebSocket.OPEN) {
    ws.send(JSON.stringify(
      {
        type: "ping"
      }
    ))
  }
}, 5000)