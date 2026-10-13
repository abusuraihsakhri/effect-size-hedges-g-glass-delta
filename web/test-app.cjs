const test = require('node:test');
const assert = require('node:assert/strict');
const {compute, batch, parseCSV} = require('./app.js');

const input = {mean1: 10, mean2: 8, std1: 2, std2: 2, n1: 30, n2: 30};

test('independent-group estimators agree with hand calculation', () => {
  const r = compute(input);
  assert.ok(Math.abs(r.cohens_d - 1) < 1e-12);
  assert.ok(Math.abs(r.hedges_g - (1 - 3 / (4 * 58 - 1))) < 1e-12);
  assert.equal(r.glasses_delta, 1);
  assert.ok(Math.abs(r.standard_error - Math.sqrt(2 / 30 + 1 / 120)) < 1e-12);
});

test('unequal sample sizes have weighted pooled SD', () => {
  const r = compute({...input, n1: 10, n2: 30, std1: 2, std2: 4});
  assert.ok(Math.abs(r.cohens_d - 2 / Math.sqrt((9 * 4 + 29 * 16) / 38)) < 1e-12);
});

test('invalid statistics produce explicit errors', () => {
  assert.throws(() => compute({...input, n1: 1}), /at least 2/);
  assert.throws(() => compute({...input, n1: 2.5}), /integers/);
  assert.throws(() => compute({...input, std2: 0}), /positive/);
  assert.throws(() => compute({...input, std1: -2}), /non-negative/);
  assert.throws(() => compute({...input, mean1: Infinity}), /finite/);
  assert.throws(() => compute({...input, mean1: ''}), /required/);
});

test('CSV parser supports quoted fields and preserves extra columns', () => {
  const text = 'mean1,mean2,std1,std2,n1,n2,note\r\n10,8,2,2,30,30,"hello, ""test"""\r\n';
  assert.equal(parseCSV(text)[1][6], 'hello, "test"');
  const result = batch(text);
  assert.equal(result.count, 1);
  const rows = parseCSV(result.csv);
  assert.equal(rows[1][6], 'hello, "test"');
  assert.equal(rows[1][7], '1.0000');
});

test('CSV errors include row number', () => {
  assert.throws(() => batch('mean1,mean2,std1,std2,n1,n2\n10,8,0,0,30,30\n'), /row 2/);
  assert.throws(() => batch('mean1,mean2,std1,std2,n1,n2\n10,8,2\n'), /row 2/);
});

test('Excel formulas from user-provided metadata are escaped on export', () => {
  const csv = batch('mean1,mean2,std1,std2,n1,n2,tag\n10,8,2,2,30,30,=1+1\n').csv;
  assert.equal(parseCSV(csv)[1][6], "'=1+1");
});
