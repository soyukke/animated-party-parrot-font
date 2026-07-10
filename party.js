const stage = document.querySelector('#stage');
const message = document.querySelector('#message');
const count = document.querySelector('#count');
let parrots = [];
const axis = document.querySelector('#axis');
const speed = document.querySelector('#speed');
const toggle = document.querySelector('#toggle');
const FIRST_FRAME = 0xE000;
const FRAME_COUNT = 10;
let playing = !matchMedia('(prefers-reduced-motion: reduce)').matches;
let start = performance.now();

function buildParrots() {
  stage.replaceChildren();
  let visible = 0;
  for (const character of message.value || 'P') {
    const span = document.createElement('span');
    if (/\s/.test(character)) {
      span.className = 'parrot-space';
    } else {
      span.className = 'parrot';
      span.dataset.source = character;
      span.setAttribute('aria-label', character);
      visible += 1;
    }
    stage.append(span);
  }
  parrots = [...stage.querySelectorAll('.parrot')];
  count.value = `${visible} PARROT${visible === 1 ? '' : 'S'}`;
  stage.setAttribute('aria-label', `${message.value}: ${visible} animated parrots`);
}

function render(now) {
  const period = 1000 / Number(speed.value);
  const value = playing ? ((now - start) % period) / period * 100 : Number(axis.value);
  if (playing) axis.value = value;
  parrots.forEach((parrot, index) => {
    const frame = Math.floor((value / 100 * FRAME_COUNT + index * 2) % FRAME_COUNT);
    parrot.textContent = String.fromCodePoint(FIRST_FRAME + frame);
    parrot.style.transform = 'none';
    parrot.style.filter = 'none';
  });
  requestAnimationFrame(render);
}
toggle.addEventListener('click', () => { playing = !playing; start = performance.now(); toggle.textContent = playing ? 'PAUSE' : 'PLAY'; });
axis.addEventListener('input', () => { playing = false; toggle.textContent = 'PLAY'; });
message.addEventListener('input', buildParrots);
buildParrots();
requestAnimationFrame(render);
