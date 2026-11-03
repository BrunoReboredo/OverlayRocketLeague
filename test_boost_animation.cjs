const test = require('node:test');
const assert = require('node:assert/strict');
const { BoostTween } = require('./boost-animation.js');

test('10 to 0 passes through intermediate values and finishes at exactly zero', () => {
  const tween = new BoostTween(200);
  tween.set('player', 10, 0);
  tween.set('player', 0, 100);
  assert.equal(tween.value('player', 100), 10);
  assert.equal(tween.value('player', 200), 5);
  assert.equal(tween.value('player', 300), 0);
  assert.equal(tween.value('player', 600), 0);
});

test('repeated API targets do not restart animation; retargeting stays continuous', () => {
  const tween = new BoostTween(200);
  tween.set('player', 10, 0);
  tween.set('player', 0, 100);
  tween.set('player', 0, 200);
  assert.equal(tween.value('player', 200), 5);
  tween.set('player', 20, 200);
  assert.equal(tween.value('player', 200), 5);
  assert.equal(tween.value('player', 300), 12.5);
  assert.equal(tween.value('player', 400), 20);
});

test('players have independent animations, no invented values before first data', () => {
  const tween = new BoostTween(200);
  tween.set('A', 80, 0);
  tween.set('B', 10, 0);
  tween.set('A', 20, 100);
  tween.set('B', 90, 100);
  assert.equal(tween.value('A', 200), 50);
  assert.equal(tween.value('B', 200), 50);
  tween.set('unknown', null, 100);
  assert.equal(tween.value('unknown', 150), null);
  tween.set('unknown', 0, 200);
  assert.equal(tween.value('unknown', 200), 0);
  tween.retain(new Set(['A']));
  assert.equal(tween.states.size, 1);
});
