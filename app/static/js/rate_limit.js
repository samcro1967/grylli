export function startRateLimitRedirect(delaySeconds, redirectUrl) {
  let delay = parseInt(delaySeconds);
  const display = document.getElementById("delay");

  const interval = setInterval(() => {
    delay--;
    if (delay <= 0) {
      clearInterval(interval);
    }
    display.innerText = delay;
  }, 1000);

  setTimeout(() => {
    window.location.href = redirectUrl;
  }, delay * 1000);
}
