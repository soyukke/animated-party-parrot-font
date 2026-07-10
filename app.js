const specimen = document.querySelector('#specimen');
const axis = document.querySelector('#axis');
const speed = document.querySelector('#speed');
const toggle = document.querySelector('#toggle');
const value = document.querySelector('#value');
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
let playing = !reduceMotion;
let origin = performance.now();

function setAxis(v) {
  axis.value = v;
  value.value = Number(v).toFixed(1);
  specimen.style.fontVariationSettings = `"ANIM" ${v}`;
}

function frame(now) {
  if (playing) {
    const period = 1000 / Number(speed.value);
    setAxis(((now - origin) % period) / period * 100);
  }
  requestAnimationFrame(frame);
}

toggle.addEventListener('click', () => {
  playing = !playing;
  origin = performance.now() - Number(axis.value) / 100 * (1000 / Number(speed.value));
  toggle.textContent = playing ? 'Pause' : 'Play';
});
axis.addEventListener('input', () => { playing = false; toggle.textContent = 'Play'; setAxis(axis.value); });
speed.addEventListener('input', () => { origin = performance.now(); });
if (reduceMotion) { toggle.textContent = 'Play'; setAxis(50); }
requestAnimationFrame(frame);
