// Checks the practice questions in web/exam.js: every question has 3-5 distinct options,
// a valid answer index, and an explanation in English and Turkish.   Run: node tests/test_exam.js
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {} };
require("../web/exam.js");
const { GRAMMAR, VOCAB, PASSAGES, PARAGRAPH } = window.ExamPractice.data;
const all = [...GRAMMAR, ...VOCAB, ...PARAGRAPH, ...PASSAGES.flatMap((p) => p.qs)];
let bad = 0;
for (const q of all) {
  const ok = q.o.length >= 3 && q.o.length <= 5 && new Set(q.o).size === q.o.length &&
    Number.isInteger(q.a) && q.a >= 0 && q.a < q.o.length && q.e && q.e.en && q.e.tr && q.q;
  if (!ok) { bad++; console.log("BAD:", q.q.slice(0, 70)); }
}
console.log(`${all.length} questions checked, ${bad} problems`);
process.exit(bad ? 1 : 0);
