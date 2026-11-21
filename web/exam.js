/* Exam practice screen for IGU's Erasmus+ English exam.
   - Info: what IGU's 2026 guides say about the exam (with pages), and the format of earlier years
   - Topics: a B2 study checklist for the sections of the exam (progress kept in this browser)
   - Practice test: 18 multiple-choice questions drawn from a pool (grammar, vocabulary, reading)
   - Writing: a task, a word counter, and feedback from the LLM (a rough level and fixes, not a grade)
   All practice questions were written for this project. They are NOT IGU's exam questions. */
(function () {
  const L = () => (typeof lang !== "undefined" && lang === "tr" ? "tr" : "en");
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pick = (o) => (o && typeof o === "object" && "en" in o ? o[L()] : o);
  const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  const SAMPLES_URL = "https://ydyo.gelisim.edu.tr/tr/akademik-icerik-ornek-sinavlar";
  const SUBJECTS_URL = "https://panel.gelisim.edu.tr/assets/2019/dokumanlar/dio/ERASMUS%20EXAM%20SUBJECTS-_36b646382e41416fbdd570e4b772a818.pdf";
  const SAMPLE_PDF_URL = "https://panel.gelisim.edu.tr/assets/2020/dokumanlar/ydyo/Erasmus%20S%C4%B1nav%C4%B1%20%C3%96rne%C4%9Fi_223b0bf0d480446fa7f973869f184677.pdf";

  /* ---------- texts ---------- */
  const T = {
    en: {
      title: "Study for IGU's Erasmus+ language exam",
      tabs: { info: "ℹ️ the exam", topics: "📚 topics", test: "✏️ practice test", writing: "📝 writing" },
      notOfficial: "The practice questions on this screen were written for this site. They are not IGU's exam questions, and the real exam may be different.",
      earlier: "Earlier years (the format changes every year)",
      earlierNote: "Speaking was part of the exam in 2024 and 2025; the 2026 guides mention a test and a writing task instead. Always check the School of Foreign Languages announcement before the exam.",
      cols: ["year", "level", "test", "other part", "negative marking"],
      samples: "IGU's sample exams page", subjectsDoc: "IGU's exam subjects document (2019)", samplePdf: "IGU's sample Erasmus exam (2020)",
      whatTested: "What each part tests (IGU's exam subjects document)",
      types: "Question types in IGU's sample exam",
      topicsIntro: "A B2-level study list for each part of the exam. Tick what you have studied; your progress stays in this browser.",
      topicsNote: "The section descriptions and question types come from IGU's exam subjects document (2019) and sample exam (2020). The detailed grammar and vocabulary lists are a general B2 study list, not an official IGU syllabus.",
      done: "done",
      testIntro: (n) => `${n} questions in the styles of IGU's sample exam: grammar (also two-blank tense questions), vocabulary, a reading passage, and paragraph questions (irrelevant sentence, same meaning, completing a paragraph). Each test draws new questions. You see the answer and an explanation after every question.`,
      start: "start the test", next: "next →", finish: "see my score", again: "new test", qOf: (i, n) => `question ${i} of ${n}`,
      correct: "✓ correct!", wrong: (a) => `✗ the answer is: ${a}`,
      score: "your score", pass: "That is at or above 60, the pass mark in IGU's guides. Keep it up ♡",
      fail: "The pass mark in IGU's guides is 60. Check the explanations below and try a new test ♡",
      bySection: "by section", review: "questions to review", noMistakes: "No mistakes. Wow ✧",
      practiceOnly: "This is practice only: the real exam is scored by IGU's School of Foreign Languages.",
      sections: { grammar: "grammar", vocab: "vocabulary", reading: "reading" },
      target: "target: 180–200 words",
      readFirst: "Read the text, then answer:",
      writingIntro: "In IGU's sample exam and exam subjects, the writing part is an essay of at least 180–200 words on a familiar, everyday topic, giving your opinion and reasons. Try to finish in about 30 minutes.",
      task: "task", another: "another task", words: (n) => `${n} words`,
      checklist: ["an introduction that answers the task and gives your opinion", "2 body paragraphs, each with a reason and an example",
        "linking words: however, moreover, for example, as a result, on the other hand", "a short conclusion", "check verb tenses, subject–verb agreement and articles"],
      getFeedback: "get feedback", thinking: "reading your text…",
      feedbackTag: "⚠ AI feedback: a rough estimate, not your exam grade",
      tooShort: "Write at least 50 words first ♡",
      error: (m) => `no feedback right now (${m}). Try again in a minute?`
    },
    tr: {
      title: "İGÜ Erasmus+ dil sınavına çalış",
      tabs: { info: "ℹ️ sınav", topics: "📚 konular", test: "✏️ deneme testi", writing: "📝 yazma" },
      notOfficial: "Bu ekrandaki deneme soruları bu site için yazıldı. İGÜ'nün sınav soruları değildir; gerçek sınav farklı olabilir.",
      earlier: "Önceki yıllar (format her yıl değişiyor)",
      earlierNote: "2024 ve 2025'te sınavda konuşma bölümü vardı; 2026 kılavuzları ise test ve yazma bölümünden bahsediyor. Sınavdan önce mutlaka Yabancı Diller Yüksekokulu'nun duyurusuna bak.",
      cols: ["yıl", "seviye", "test", "diğer bölüm", "yanlış doğruyu götürür mü"],
      samples: "İGÜ örnek sınavlar sayfası", subjectsDoc: "İGÜ sınav konuları belgesi (2019)", samplePdf: "İGÜ örnek Erasmus sınavı (2020)",
      whatTested: "Her bölüm neyi ölçüyor (İGÜ sınav konuları belgesi)",
      types: "İGÜ örnek sınavındaki soru tipleri",
      topicsIntro: "Sınavın her bölümü için B2 seviyesinde bir çalışma listesi. Çalıştıklarını işaretle; ilerlemen bu tarayıcıda kalır.",
      topicsNote: "Bölüm açıklamaları ve soru tipleri İGÜ'nün sınav konuları belgesinden (2019) ve örnek sınavından (2020) geliyor. Ayrıntılı dil bilgisi ve kelime listeleri genel bir B2 çalışma listesi; İGÜ'nün resmi müfredatı değil.",
      done: "tamam",
      testIntro: (n) => `İGÜ örnek sınavındaki tiplerde ${n} soru: dil bilgisi (iki boşluklu zaman soruları dahil), kelime, bir okuma parçası ve paragraf soruları (anlamı bozan cümle, aynı anlamdaki cümle, paragraf tamamlama). Her test yeni sorular seçer. Her sorudan sonra doğru cevabı ve açıklamasını görürsün.`,
      start: "teste başla", next: "sonraki →", finish: "puanımı gör", again: "yeni test", qOf: (i, n) => `soru ${i} / ${n}`,
      correct: "✓ doğru!", wrong: (a) => `✗ doğru cevap: ${a}`,
      score: "puanın", pass: "Bu, İGÜ kılavuzlarındaki geçme puanı olan 60'ın üstünde. Böyle devam ♡",
      fail: "İGÜ kılavuzlarına göre geçme puanı 60. Aşağıdaki açıklamalara bak ve yeni bir test dene ♡",
      bySection: "bölümlere göre", review: "tekrar etmen gereken sorular", noMistakes: "Hiç yanlış yok. Vay ✧",
      practiceOnly: "Bu sadece bir alıştırma: gerçek sınavı İGÜ Yabancı Diller Yüksekokulu puanlar.",
      sections: { grammar: "dil bilgisi", vocab: "kelime", reading: "okuma" },
      target: "hedef: 180–200 kelime",
      readFirst: "Metni oku, sonra cevapla:",
      writingIntro: "İGÜ'nün örnek sınavında ve sınav konuları belgesinde yazma bölümü, günlük hayattan tanıdık bir konuda görüşünü ve nedenlerini anlattığın en az 180–200 kelimelik bir deneme yazısı. Yaklaşık 30 dakikada bitirmeye çalış.",
      task: "konu", another: "başka konu", words: (n) => `${n} kelime`,
      checklist: ["konuya cevap veren ve görüşünü söyleyen bir giriş", "her birinde bir neden ve bir örnek olan 2 gelişme paragrafı",
        "bağlaçlar: however, moreover, for example, as a result, on the other hand", "kısa bir sonuç", "fiil zamanlarını, özne–fiil uyumunu ve artikelleri kontrol et"],
      getFeedback: "geri bildirim al", thinking: "yazını okuyorum…",
      feedbackTag: "⚠ yapay zekâ geri bildirimi: kaba bir tahmin, sınav notun değil",
      tooShort: "Önce en az 50 kelime yaz ♡",
      error: (m) => `şu an geri bildirim veremiyorum (${m}). Bir dakika sonra tekrar dener misin?`
    }
  };
  const t = (k) => T[L()][k];

  /* ---------- what IGU's documents say (with pages) ---------- */
  const INFO = [
    { icon: "📅", en: "<b>Date:</b> 11 March 2026, held by IGU's School of Foreign Languages. Exam times are announced on its website.",
      tr: "<b>Tarih:</b> 11 Mart 2026, İGÜ Yabancı Diller Yüksekokulu tarafından. Sınav saatleri yüksekokulun sitesinde duyurulur.",
      src: ["igu-study-2026:3", "igu-internship-2026:3"] },
    { icon: "🧩", en: "<b>Format (2026):</b> two parts. A <b>test</b> with multiple-choice questions in 3 parts: <b>grammar, vocabulary and reading</b>. Then a <b>writing task</b>. If you do not complete both parts, the exam is invalid.",
      tr: "<b>Format (2026):</b> iki bölüm. Üç kısımlı çoktan seçmeli bir <b>test</b>: <b>dil bilgisi, kelime ve okuma</b>. Ardından bir <b>yazma görevi</b>. İki bölümü de tamamlamazsan sınav geçersiz sayılır.",
      src: ["igu-study-2026:3", "igu-internship-2026:3"] },
    { icon: "🎯", en: "<b>Pass mark:</b> at least 60 out of 100.", tr: "<b>Geçme puanı:</b> 100 üzerinden en az 60.",
      src: ["igu-study-2026:3", "igu-internship-2026:3"] },
    { icon: "📊", en: "<b>Why it matters:</b> your language score is 50% of your Erasmus score; your GPA is the other 50%. The total must be at least 60.",
      tr: "<b>Neden önemli:</b> dil puanın Erasmus puanının %50'si; diğer %50 not ortalaman. Toplam en az 60 olmalı.",
      src: ["igu-study-2026:6", "igu-internship-2026:7"] },
    { icon: "🎓", en: "<b>Exemption:</b> with at least 60 in YDS, YÖKDİL or an international exam that ÖSYM accepts, you upload the result and do not take the exam.",
      tr: "<b>Muafiyet:</b> YDS, YÖKDİL ya da ÖSYM'nin kabul ettiği uluslararası bir sınavdan en az 60 aldıysan belgeni yüklersin, sınava girmezsin.",
      src: ["igu-study-2026:6", "igu-internship-2026:3"] },
    { icon: "⚠️", en: "<b>Don't skip it:</b> if you say you will take the exam and then don't, 5 points are deducted in your next application.",
      tr: "<b>Kaçırma:</b> sınava gireceğini söyleyip girmezsen bir sonraki başvurunda 5 puan düşülür.",
      src: ["igu-study-2026:3", "igu-internship-2026:3"] },
    { icon: "🪪", en: "<b>On the day:</b> bring your student ID card.", tr: "<b>Sınav günü:</b> öğrenci kartını yanında getir.", src: ["igu-study-2026:3"] }
  ];
  const PARTS = [     // IGU's exam subjects document (2019), summarised
    { en: "<b>Listening</b> (in earlier years): the main topic and details of dialogues.", tr: "<b>Dinleme</b> (önceki yıllarda): diyaloglardaki genel konu ve ayrıntılar." },
    { en: "<b>Vocabulary:</b> everyday words from A2 to B2, used in daily-life situations.", tr: "<b>Kelime:</b> A2'den B2'ye günlük hayatta kullanılan kelimeler." },
    { en: "<b>Grammar:</b> multiple-choice questions on using grammar in academic and everyday contexts.", tr: "<b>Dil bilgisi:</b> kuralların akademik ve günlük bağlamda kullanımını ölçen çoktan seçmeli sorular." },
    { en: "<b>Reading:</b> the main idea, details, guessing word meanings from the text, and inference.", tr: "<b>Okuma:</b> ana fikir, ayrıntılar, kelime anlamını metinden çıkarma ve çıkarım yapma." },
    { en: "<b>Writing:</b> an essay of at least 180–200 words on one of several familiar everyday topics.", tr: "<b>Yazma:</b> verilen tanıdık günlük konulardan biri üzerine en az 180–200 kelimelik bir deneme." }
  ];
  const TYPES = [     // the kinds of questions in IGU's sample exam (2020), described in my own words
    { en: "a short text with gaps: choose the right word (3 options)", tr: "boşluklu kısa metin: doğru kelimeyi seç (3 şık)" },
    { en: "sentences with two blanks for verb tenses (5 options, A–E)", tr: "iki boşluklu zaman cümleleri (5 şık, A–E)" },
    { en: "a reading passage with questions", tr: "okuma parçası ve soruları" },
    { en: "completing a paragraph with the missing sentence", tr: "paragrafı eksik cümleyle tamamlama" },
    { en: "finding the irrelevant sentence in a paragraph", tr: "paragrafta anlamı bozan cümleyi bulma" },
    { en: "choosing the sentence with the same meaning", tr: "aynı anlamdaki cümleyi seçme" },
    { en: "writing an essay of at least 180–200 words, giving reasons", tr: "en az 180–200 kelimelik, nedenleriyle bir deneme yazma" }
  ];
  const EARLIER = [   // from the School of Foreign Languages' exam documents and announcements
    { year: "2019", level: { en: "vocabulary A2–B2", tr: "kelime A2–B2" }, test: { en: "listening, vocabulary, grammar, reading (120 min with writing)", tr: "dinleme, kelime, dil bilgisi, okuma (yazmayla birlikte 120 dk)" },
      other: { en: "writing, 180–200+ words", tr: "yazma, en az 180–200 kelime" }, neg: { en: "not stated", tr: "belirtilmemiş" } },
    { year: "2024", level: "B2", test: { en: "grammar 20, vocabulary 20, reading 20 questions (60 pts)", tr: "dil bilgisi 20, kelime 20, okuma 20 soru (60 puan)" },
      other: { en: "speaking, 2–5 min (40 pts)", tr: "konuşma, 2–5 dk (40 puan)" }, neg: { en: "no", tr: "hayır" } },
    { year: "2025", level: "B2", test: { en: "grammar, vocabulary, reading, listening: 10 questions each (60 pts, 60 min)", tr: "dil bilgisi, kelime, okuma, dinleme: 10'ar soru (60 puan, 60 dk)" },
      other: { en: "speaking, 2–5 min (40 pts)", tr: "konuşma, 2–5 dk (40 puan)" }, neg: { en: "no", tr: "hayır" } }
  ];
  const SRC_LABEL = {
    en: { "igu-study-2026": "IGU study guide 2026", "igu-internship-2026": "IGU traineeship guide 2026" },
    tr: { "igu-study-2026": "İGÜ öğrenim kılavuzu 2026", "igu-internship-2026": "İGÜ staj kılavuzu 2026" }
  };
  const srcChip = (s) => { const [k, p] = s.split(":"); return `<span class="src">${esc(SRC_LABEL[L()][k])} · ${L() === "tr" ? "s." : "p."}${p}</span>`; };

  /* ---------- B2 study checklist ---------- */
  const TOPICS = [
    { id: "g", title: { en: "Grammar (language structure)", tr: "Dil bilgisi (dil yapısı)" }, items: [
      "Tenses: present / past / future, simple, continuous and perfect", "Two-blank tense questions: which tenses fit together (since…, by the time…, when…)", "Future perfect and past perfect continuous",
      "Conditionals 0–3 and mixed conditionals", "wish / if only / it's high time", "Passive voice, also with modals (must be done)",
      "Modals: obligation, advice, deduction (must have, can't have)", "Relative clauses: who, whom, whose, which, that, where",
      "Reported speech and indirect questions (where the office was)", "Gerunds and infinitives (look forward to doing, decide to do)",
      "Comparatives and 'the more…, the better…'", "Linkers: although, despite, however, whereas, unless",
      "Inversion: not only…, hardly…, never before…", "Causative: have / get something done", "Articles, quantifiers and subject–verb agreement"] },
    { id: "v", title: { en: "Vocabulary", tr: "Kelime bilgisi" }, items: [
      "Word formation: -tion, -ment, -ness, -ive, -able, un-, dis-, mis-", "Collocations: meet a deadline, take part in, make progress",
      "Phrasal verbs: fill in, put off, carry out, look into, set up", "Confusing pairs: experience / experiment, affect / effect, rise / raise",
      "Academic words: apply, require, assess, available, significant", "Themes: education, travel, work, technology, environment, culture"] },
    { id: "r", title: { en: "Reading", tr: "Okuma" }, items: [
      "Main idea and title of a passage", "Specific details (scanning)", "Inference: what the writer suggests but does not say",
      "Vocabulary in context", "Reference: what 'it', 'they', 'this' refer to", "The writer's purpose and attitude",
      "Finding the irrelevant sentence in a paragraph", "Completing a paragraph with the missing sentence", "Choosing the sentence with the same meaning"] },
    { id: "w", title: { en: "Writing", tr: "Yazma" }, items: [
      "Opinion essay of at least 180–200 words: introduction, 2 body paragraphs, conclusion", "Topic sentences, reasons and examples",
      "Linking words for adding, contrasting and giving results", "Checking your own mistakes in 5 minutes"] }
  ];

  /* ---------- question pool (original questions) ---------- */
  const GRAMMAR = [
    { q: "If I ___ more time, I would apply for a study mobility in Spain.", o: ["have", "had", "will have", "would have"], a: 1,
      e: { en: "Second conditional (an unreal situation now): if + past simple, would + verb.", tr: "İkinci tip koşul (şu an gerçek olmayan durum): if + geçmiş zaman, would + fiil." } },
    { q: "By the time she arrives in Rome, the orientation meeting ___.", o: ["will have finished", "has finished", "finishes", "is finishing"], a: 0,
      e: { en: "Future perfect: an action completed before a point in the future ('by the time…').", tr: "Future perfect: gelecekteki bir andan önce bitmiş olacak eylem ('by the time…')." } },
    { q: "The application form ___ online before 28 February.", o: ["must submit", "must be submitted", "must submitting", "must to submit"], a: 1,
      e: { en: "Passive with a modal: modal + be + past participle. The form does not submit itself.", tr: "Modal ile edilgen yapı: modal + be + V3. Formu biri gönderir, form kendini göndermez." } },
    { q: "I'm looking forward to ___ from the host university.", o: ["hear", "hearing", "heard", "be heard"], a: 1,
      e: { en: "'look forward to' ends with the preposition 'to', so the verb takes -ing.", tr: "'look forward to' bir edatla (to) biter; ardından fiil -ing alır." } },
    { q: "The professor ___ I met in Pisa wrote me a reference letter.", o: ["whose", "which", "whom", "what"], a: 2,
      e: { en: "'whom' is the object form for people (I met him → whom I met). 'which' is for things.", tr: "'whom' insanlar için nesne hâlidir (I met him → whom I met). 'which' nesneler içindir." } },
    { q: "She ___ in Italy for six months when she finally got used to the food.", o: ["has lived", "had been living", "lives", "will live"], a: 1,
      e: { en: "Past perfect continuous: an action that continued up to a moment in the past.", tr: "Past perfect continuous: geçmişteki bir ana kadar süregelen eylem." } },
    { q: "You ___ forget to bring your student ID card to the exam.", o: ["mustn't", "don't have to", "needn't", "might"], a: 0,
      e: { en: "'mustn't' = it is not allowed. 'don't have to' and 'needn't' mean it is not necessary.", tr: "'mustn't' = yasak/yapmamalısın. 'don't have to' ve 'needn't' = gerekli değil." } },
    { q: "Not only ___ the exam, but she also got the highest score.", o: ["she passed", "did she pass", "she did pass", "passed she"], a: 1,
      e: { en: "After 'Not only' at the start of a sentence, use question word order (inversion): did she pass.", tr: "Cümle 'Not only' ile başlarsa soru düzeni (devrik yapı) gelir: did she pass." } },
    { q: "My coordinator suggested that I ___ for the internship as early as possible.", o: ["apply", "to apply", "applying", "will apply"], a: 0,
      e: { en: "'suggest that + subject + base verb' (apply). 'suggest to apply' is not correct.", tr: "'suggest that + özne + yalın fiil' (apply). 'suggest to apply' yanlıştır." } },
    { q: "The more you practise speaking, ___ you will become.", o: ["the more confident", "more confident", "the most confident", "most confident"], a: 0,
      e: { en: "Double comparative: the + comparative…, the + comparative.", tr: "Çift karşılaştırma: the + -er/more…, the + -er/more." } },
    { q: "I wish I ___ Italian before I moved to Pisa.", o: ["learnt", "had learnt", "have learnt", "would learn"], a: 1,
      e: { en: "A regret about the past: wish + past perfect.", tr: "Geçmişle ilgili pişmanlık: wish + past perfect." } },
    { q: "___ the long train journey, we arrived in Vienna on time.", o: ["Although", "Despite", "However", "Because of"], a: 1,
      e: { en: "'Despite' + noun phrase. 'Although' needs a full clause (although the journey was long).", tr: "'Despite' + isim öbeği. 'Although' ardından tam cümle ister (although the journey was long)." } },
    { q: "She asked me where ___.", o: ["was the International Office", "the International Office was", "is the International Office", "the International Office is being"], a: 1,
      e: { en: "Indirect questions use statement word order (subject + verb), and the tense moves back after 'asked'.", tr: "Dolaylı sorularda düz cümle sırası kullanılır (özne + fiil); 'asked' sonrası zaman bir geri gider." } },
    { q: "The grant ___ to your bank account within 30 days.", o: ["will be paid", "will pay", "is paying", "pays"], a: 0,
      e: { en: "Passive: the grant does not pay; someone pays it. will + be + past participle.", tr: "Edilgen: hibe ödemez, ödenir. will + be + V3." } },
    { q: "Neither the students nor the coordinator ___ aware of the new deadline.", o: ["were", "was", "are", "be"], a: 1,
      e: { en: "With 'neither… nor…', the verb agrees with the nearer subject: the coordinator → was.", tr: "'neither… nor…' yapısında fiil yakındaki özneye uyar: the coordinator → was." } },
    { q: "It's high time we ___ our accommodation for the exchange semester.", o: ["book", "booked", "will book", "have booked"], a: 1,
      e: { en: "'It's high time + subject + past simple' talks about something that should happen now.", tr: "'It's high time + özne + geçmiş zaman': artık yapılması gereken bir şey." } },
    { q: "I'm going to have my passport ___ next week.", o: ["renew", "renewed", "renewing", "to renew"], a: 1,
      e: { en: "Causative: have + object + past participle (someone else renews it for you).", tr: "Ettirgen yapı: have + nesne + V3 (işi senin için başkası yapar)." } },
    { q: "Since she ---- to Pisa, she ---- three Italian courses.", o: ["moved / has taken", "has moved / took", "moves / had taken", "had moved / takes", "was moving / will take"], a: 0,
      e: { en: "since + past simple (when it started), main clause in present perfect (up to now).", tr: "since + geçmiş zaman (başlangıç anı), ana cümle present perfect (şimdiye kadar)." } },
    { q: "When the results ---- last week, most of the students ---- for hours.", o: ["were announced / had been waiting", "are announced / waited", "have been announced / wait", "announced / have waited", "had announced / were waiting"], a: 0,
      e: { en: "'last week' → past; the results were announced (passive). The waiting had gone on before that → past perfect continuous.", tr: "'last week' → geçmiş; sonuçlar açıklandı (edilgen). Bekleme ondan önce sürüyordu → past perfect continuous." } },
    { q: "If the university ---- more partner schools, more students ---- abroad every year.", o: ["had / could go", "has / would have gone", "had had / can go", "will have / went", "would have / could have gone"], a: 0,
      e: { en: "An unreal present situation: if + past simple, could/would + verb.", tr: "Şu an gerçek olmayan durum: if + geçmiş zaman, could/would + fiil." } },
    { q: "By the end of next month, the coordinator ---- all the learning agreements, so we ---- our courses soon after.", o: ["will have signed / can start", "signed / started", "has signed / would start", "had signed / will have started", "would sign / have started"], a: 0,
      e: { en: "'By the end of next month' → future perfect for the first blank; the result is a present/future possibility.", tr: "'By the end of next month' → ilk boşluk future perfect; sonuç şimdiki/gelecek bir olasılık." } },
    { q: "Hardly ___ the plane landed when it started to rain.", o: ["the plane had", "had the plane", "the plane has", "has the plane"], a: 1,
      e: { en: "'Hardly… when…' at the start: inversion with past perfect (had the plane landed).", tr: "Cümle başında 'Hardly… when…': past perfect ile devrik yapı (had the plane landed)." } }
  ];
  const VOCAB = [
    { q: "Please make sure you ___ the deadline, because late applications are not accepted.", o: ["meet", "reach", "make", "do"], a: 0,
      e: { en: "Collocation: meet a deadline.", tr: "Eşdizim: meet a deadline (son tarihe yetişmek)." } },
    { q: "Her internship gave her valuable ___ in digital marketing.", o: ["experience", "experiment", "expert", "expertly"], a: 0,
      e: { en: "experience = what you learn by doing. experiment = a scientific test.", tr: "experience = deneyim. experiment = bilimsel deney." } },
    { q: "Before you leave, you should ___ a learning agreement with both universities.", o: ["sign", "write down", "take part", "put off"], a: 0,
      e: { en: "You sign an agreement. 'put off' = postpone; 'take part' needs 'in'.", tr: "Anlaşma imzalanır (sign). 'put off' = ertelemek; 'take part' ardından 'in' ister." } },
    { q: "The lecture was so ___ that half of the students fell asleep.", o: ["boring", "bored", "bore", "boredom"], a: 0,
      e: { en: "-ing adjectives describe the thing (a boring lecture); -ed adjectives describe how people feel (bored students).", tr: "-ing sıfatlar şeyi anlatır (boring lecture); -ed sıfatlar kişinin hissini anlatır (bored students)." } },
    { q: "Living abroad helped him become more ___ and confident.", o: ["independent", "dependent", "depending", "independence"], a: 0,
      e: { en: "An adjective is needed after 'become more', and the meaning is 'able to manage alone'.", tr: "'become more' sonrası sıfat gerekir; anlam 'kendi başına idare edebilen'." } },
    { q: "If you have any questions, don't ___ to contact the International Office.", o: ["hesitate", "doubt", "wonder", "delay"], a: 0,
      e: { en: "Fixed phrase: don't hesitate to contact us.", tr: "Kalıp ifade: don't hesitate to contact us (çekinmeden yazın)." } },
    { q: "The host family made me feel very ___ from the first day.", o: ["welcome", "welcoming", "welcomes", "welcomeness"], a: 0,
      e: { en: "Fixed phrase: make someone feel welcome. 'welcoming' describes the family, not how you feel.", tr: "Kalıp: make someone feel welcome. 'welcoming' aileyi anlatır, senin hissini değil." } },
    { q: "Our flight was ___ because of heavy snow, so we took the train instead.", o: ["cancelled", "cancelling", "canceller", "cancellation"], a: 0,
      e: { en: "Passive (was + past participle): the flight was cancelled.", tr: "Edilgen (was + V3): uçuş iptal edildi." } },
    { q: "Please ___ the form carefully before you submit it.", o: ["fill in", "fill up", "fill on", "fill of"], a: 0,
      e: { en: "fill in (or fill out) a form. 'fill up' is for a tank or a glass.", tr: "Form doldurmak: fill in (ya da fill out). 'fill up' depo/bardak doldurmak içindir." } },
    { q: "Erasmus+ students are encouraged to ___ the local culture and make new friends.", o: ["explore", "exploit", "explode", "expose"], a: 0,
      e: { en: "explore = discover and learn about. exploit = use unfairly.", tr: "explore = keşfetmek. exploit = sömürmek." } },
    { q: "A ___ is a short document that summarises your education, skills and work experience.", o: ["CV", "transcript", "certificate", "receipt"], a: 0,
      e: { en: "A transcript lists your courses and grades; a CV summarises you.", tr: "Transcript ders ve notlarını listeler; CV seni özetler." } },
    { q: "The new rules will have a big ___ on how students are selected.", o: ["effect", "affect", "effective", "effectively"], a: 0,
      e: { en: "'effect' is the noun (have an effect on); 'affect' is the verb.", tr: "'effect' isimdir (have an effect on); 'affect' fiildir." } },
    { q: "The university has decided to ___ the meeting until next week because the room is not available.", o: ["put off", "put on", "put up", "put in"], a: 0,
      e: { en: "put off = postpone.", tr: "put off = ertelemek." } },
    { q: "Applicants are ___ to upload a transcript signed by the Office of Student Affairs.", o: ["required", "requiring", "requirement", "require"], a: 0,
      e: { en: "be required to do something = must do it.", tr: "be required to = yapmak zorunda olmak." } }
  ];
  const PASSAGES = [
    { text: "When Elif arrived in Lisbon for her Erasmus semester, she expected the biggest challenge to be the language. In fact, most of her lectures were in English, and her classmates were happy to help her with Portuguese. What surprised her was how different the teaching style was. At her home university, exams decided almost the whole grade. In Lisbon, students had to give presentations, write short reports every two weeks and take part in group projects. At first, Elif found this exhausting, because she was used to studying alone the night before an exam. By the end of the semester, however, she realised that working regularly had helped her remember more, and her group projects had given her friends from six different countries. She now tells other students that Erasmus is not only about a new city, but also about a new way of learning.",
      qs: [
        { q: "What is the passage mainly about?", o: ["How Elif learned Portuguese quickly", "How Elif got used to a different way of studying", "Why exams are better than group projects", "How to find accommodation in Lisbon"], a: 1,
          e: { en: "Most sentences describe the teaching style and how Elif's view of it changed.", tr: "Cümlelerin çoğu öğretim tarzını ve Elif'in bu konudaki fikrinin nasıl değiştiğini anlatıyor." } },
        { q: "What did Elif expect to be the most difficult part?", o: ["the language", "group projects", "the food", "the exams"], a: 0,
          e: { en: "'she expected the biggest challenge to be the language'.", tr: "Metinde: 'she expected the biggest challenge to be the language'." } },
        { q: "The word \"exhausting\" is closest in meaning to:", o: ["very tiring", "very exciting", "very cheap", "very easy"], a: 0,
          e: { en: "She was used to studying only before exams, so working all the time made her tired.", tr: "Sadece sınavdan önce çalışmaya alışkındı; sürekli çalışmak onu yordu." } },
        { q: "What can be inferred from the passage?", o: ["Elif failed some of her courses", "Elif's opinion of the teaching style changed over time", "Elif's classmates did not speak English", "Elif still prefers studying the night before an exam"], a: 1,
          e: { en: "'At first… exhausting… By the end… she realised…': her view changed.", tr: "'At first… exhausting… By the end… she realised…': fikri zamanla değişti." } }
      ] },
    { text: "Every year, thousands of Erasmus+ participants travel across Europe by plane. To reduce the environmental impact of these journeys, the programme supports \"green travel\": using low-emission transport such as trains, buses or shared cars for the main part of the trip. Students who choose green travel can receive a higher travel grant, and they may also get extra days of support to cover the longer journey. Critics point out that a train from Istanbul to central Europe can take several days and may cost more than a budget flight. Supporters reply that the journey itself can be part of the experience: travellers see more countries, meet other passengers and arrive less stressed than after a crowded airport. In the end, the choice depends on each student's time, budget and priorities.",
      qs: [
        { q: "What is the main purpose of the passage?", o: ["To advertise a budget airline", "To explain green travel and different opinions about it", "To prove that trains are always cheaper", "To describe student life in central Europe"], a: 1,
          e: { en: "It defines green travel, then gives the critics' and the supporters' views.", tr: "Önce yeşil seyahati tanımlıyor, sonra eleştirenlerin ve destekleyenlerin görüşlerini veriyor." } },
        { q: "Which is NOT given as an example of green travel?", o: ["trains", "buses", "shared cars", "budget flights"], a: 3,
          e: { en: "Flights are the opposite example; green travel is trains, buses or shared cars.", tr: "Uçak tam tersi örnek; yeşil seyahat tren, otobüs ya da paylaşılan araba." } },
        { q: "What do critics say about green travel?", o: ["It is too comfortable", "It can take a long time and cost more", "It is not allowed for students", "It gives a lower grant"], a: 1,
          e: { en: "'can take several days and may cost more than a budget flight'.", tr: "Metinde: 'can take several days and may cost more than a budget flight'." } },
        { q: "In \"they may also get extra days\", the word \"they\" refers to:", o: ["students who choose green travel", "critics", "budget airlines", "countries"], a: 0,
          e: { en: "The sentence starts with 'Students who choose green travel…'.", tr: "Cümle 'Students who choose green travel…' diye başlıyor." } }
      ] }
  ];
  const PARAGRAPH = [
    { q: "Find the irrelevant sentence: (I) Erasmus+ students often find it hard to manage money in a new country. (II) Rent and food can cost much more than at home. (III) Opening a local bank account can help them avoid high card fees. (IV) The programme is named after a Dutch scholar of the Renaissance. (V) Many students also use budgeting apps to track their spending.",
      o: ["I", "II", "III", "IV", "V"], a: 3, keepOrder: true,
      e: { en: "The paragraph is about managing money; sentence IV is about the programme's name.", tr: "Paragraf para yönetimini anlatıyor; IV. cümle programın adıyla ilgili." } },
    { q: "Find the irrelevant sentence: (I) Learning a few phrases of the local language makes daily life abroad much easier. (II) Shopkeepers and neighbours are usually pleased when you try. (III) Many universities offer free language courses for exchange students. (IV) Train tickets in Europe are often cheaper if you book them early. (V) Even simple greetings can help you make new friends.",
      o: ["I", "II", "III", "IV", "V"], a: 3, keepOrder: true,
      e: { en: "All the sentences are about learning the local language except IV, which is about train tickets.", tr: "Tüm cümleler yerel dili öğrenmekle ilgili; IV. cümle tren biletlerinden bahsediyor." } },
    { q: "Choose the sentence closest in meaning: \"Students are not allowed to apply for study mobility in their final year.\"",
      o: ["Final-year students may apply for study mobility only once.", "Study mobility is not open to students in their last year.", "Students must finish their final year before they study abroad.", "Only final-year students can apply for study mobility.", "Students in their last year are encouraged to apply for study mobility."], a: 1,
      e: { en: "'not allowed… in their final year' = not open to students in their last year.", tr: "'not allowed… in their final year' = son sınıf öğrencilerine açık değil." } },
    { q: "Choose the sentence closest in meaning: \"Hardly had I arrived at the dormitory when my roommate invited me to dinner.\"",
      o: ["My roommate invited me to dinner as soon as I arrived at the dormitory.", "I arrived at the dormitory long after my roommate's dinner.", "I hardly ever have dinner with my roommate.", "My roommate arrived at the dormitory before I invited her to dinner.", "I invited my roommate to dinner because I had arrived late."], a: 0,
      e: { en: "'Hardly had… when…' = one thing happened immediately after the other.", tr: "'Hardly had… when…' = bir şey olur olmaz diğeri oldu." } },
    { q: "Complete the paragraph: \"Many students worry that they will feel lonely during their first weeks abroad. ---- Orientation days, buddy programmes and student clubs are organised for exactly this reason, and most students say they made their first friends there.\"",
      o: ["However, host universities usually do a lot to help newcomers meet people.", "Therefore, it is better to stay at home and study online.", "The weather in northern Europe is often cold and rainy.", "Some students prefer to travel by train instead of by plane.", "As a result, loneliness is never a problem for exchange students."], a: 0,
      e: { en: "The next sentence gives examples of help (orientation, buddies, clubs), so the missing sentence must introduce that help.", tr: "Sonraki cümle yardım örnekleri veriyor (oryantasyon, buddy, kulüpler); eksik cümle bu yardımı tanıtmalı." } },
    { q: "Complete the paragraph: \"Writing a good motivation letter takes time. ---- Then they should explain how the exchange fits their studies and future plans, and finish with a short, polite closing.\"",
      o: ["First, applicants should say clearly why they chose this programme.", "Motivation letters are not required by every university.", "Some letters are written by hand, others on a computer.", "The deadline for most letters has already passed.", "In fact, nobody reads motivation letters carefully."], a: 0,
      e: { en: "'Then…' needs a first step before it: 'First, applicants should…'.", tr: "'Then…' öncesinde bir ilk adım ister: 'First, applicants should…'." } }
  ];

  const WRITING_TASKS = [
    "Why do you want to take part in Erasmus+? Explain how it would help your studies and your future career.",
    "Some people say that studying abroad is more useful than studying in your own country. Do you agree? Give reasons and examples.",
    "Should university students do an internship before they graduate? Why or why not?",
    "What are the advantages and disadvantages of online learning for university students?",
    "Technology makes us more connected but also lonelier. To what extent do you agree?",
    "What can universities do to help international students feel at home?",
    "Describe a difficult situation you have faced and explain what you learned from it.",
    "Is it better to travel alone or with friends? Discuss both views and give your opinion.",
    "Some people prefer to live in a big city, others in a small town. Which do you prefer? Give reasons for your answer.",
    "Do you think social media has a positive or a negative effect on young people? Give reasons for your answer."
  ];

  /* ---------- state ---------- */
  let root = null, tab = "info", test = null, taskIndex = Math.floor(Math.random() * WRITING_TASKS.length);
  const resize = () => { if (typeof resizeFrame === "function") resizeFrame(); };

  function mixOptions(x) {          // a new option order every time, so the answer is not always "a"
    if (x.keepOrder) return { ...x };                 // I-V stay in order
    const order = shuffle(x.o.map((_, k) => k));
    return { ...x, o: order.map((k) => x.o[k]), a: order.indexOf(x.a) };
  }

  function newTest() {
    const passage = PASSAGES[Math.floor(Math.random() * PASSAGES.length)];
    const items = [
      ...shuffle(GRAMMAR).slice(0, 8).map((x) => ({ ...mixOptions(x), s: "grammar" })),
      ...shuffle(VOCAB).slice(0, 6).map((x) => ({ ...mixOptions(x), s: "vocab" })),
      ...passage.qs.map((x) => ({ ...mixOptions(x), s: "reading", passage: passage.text })),
      ...shuffle(PARAGRAPH).slice(0, 2).map((x) => ({ ...mixOptions(x), s: "reading" }))
    ];
    return { items, i: -1, answers: [] };
  }

  /* ---------- rendering ---------- */
  function render() {
    const tabs = Object.entries(t("tabs")).map(([k, v]) =>
      `<button type="button" data-tab="${k}" aria-selected="${tab === k}">${v}</button>`).join("");
    const icon = typeof sprite === "function" ? sprite("passport", 3) : "";
    root.innerHTML = `<h2>${icon}${esc(t("title"))}</h2><div class="tabs" role="tablist">${tabs}</div><div id="exam-body"></div>`;
    root.querySelectorAll("[data-tab]").forEach((b) => b.onclick = () => { tab = b.dataset.tab; render(); });
    const body = root.querySelector("#exam-body");
    ({ info: renderInfo, topics: renderTopics, test: renderTest, writing: renderWriting })[tab](body);
    resize();
  }

  function renderInfo(body) {
    const cards = INFO.map((c) => `<div class="card">${c.icon} ${c[L()]}<br>${c.src.map(srcChip).join("")}</div>`).join("");
    const rows = EARLIER.map((r) => `<tr><td>${r.year}</td><td>${esc(pick(r.level))}</td><td>${esc(pick(r.test))}</td><td>${esc(pick(r.other))}</td><td>${esc(pick(r.neg))}</td></tr>`).join("");
    body.innerHTML = `${cards}
      <h3>${esc(t("earlier"))}</h3>
      <table><tr>${t("cols").map((c) => `<th>${esc(c)}</th>`).join("")}</tr>${rows}</table>
      <p>${esc(t("earlierNote"))}</p>
      <h3>${esc(t("whatTested"))}</h3><ul>${PARTS.map((x) => `<li>${x[L()]}</li>`).join("")}</ul>
      <h3>${esc(t("types"))}</h3><ul>${TYPES.map((x) => `<li>${esc(pick(x))}</li>`).join("")}</ul>
      <p>🔗 <a href="${SUBJECTS_URL}" target="_blank" rel="noopener">${esc(t("subjectsDoc"))}</a><br>
         🔗 <a href="${SAMPLE_PDF_URL}" target="_blank" rel="noopener">${esc(t("samplePdf"))}</a><br>
         🔗 <a href="${SAMPLES_URL}" target="_blank" rel="noopener">${esc(t("samples"))}</a></p>
      <div class="card note">${esc(t("notOfficial"))}</div>`;
  }

  function renderTopics(body) {
    const done = store.get("examTopics", {});
    let total = 0, ticked = 0;
    const groups = TOPICS.map((g) => {
      const items = g.items.map((item, k) => {
        const id = `${g.id}${k}`; total++; if (done[id]) ticked++;
        return `<label class="topic"><input type="checkbox" data-id="${id}" ${done[id] ? "checked" : ""}><span>${esc(item)}</span></label>`;
      }).join("");
      return `<h3>${esc(pick(g.title))}</h3>${items}`;
    }).join("");
    body.innerHTML = `<p>${esc(t("topicsIntro"))}</p>
      <div class="meta"><span>${ticked} / ${total} ${esc(t("done"))}</span></div>
      <div class="bar"><span style="width:${Math.round(100 * ticked / total)}%"></span></div>
      ${groups}<div class="card note">${esc(t("topicsNote"))}</div>`;
    body.querySelectorAll("input[type=checkbox]").forEach((cb) => cb.onchange = () => {
      const d = store.get("examTopics", {}); d[cb.dataset.id] = cb.checked; store.set("examTopics", d);
      renderTopics(body); resize();
    });
  }

  function renderTest(body) {
    if (!test || test.i === -1) {
      const n = 8 + 6 + 4 + 2;
      body.innerHTML = `<p>${esc(t("testIntro")(n))}</p><button type="button" class="btn main" id="start">${esc(t("start"))}</button>
        <div class="card note" style="margin-top:10px">${esc(t("notOfficial"))}</div>`;
      body.querySelector("#start").onclick = () => { test = newTest(); test.i = 0; renderTest(body); resize(); };
      return;
    }
    if (test.i >= test.items.length) return renderScore(body);
    const item = test.items[test.i], answered = test.answers[test.i];
    const passage = item.passage ? `<div class="passage"><b>${esc(t("readFirst"))}</b><br>${esc(item.passage)}</div>` : "";
    const opts = item.o.map((o, k) => {
      let cls = "";
      if (answered !== undefined) cls = k === item.a ? "right" : (k === answered ? "wrong" : "");
      return `<button type="button" data-k="${k}" class="${cls}" ${answered !== undefined ? "disabled" : ""}>${"abcde"[k]}) ${esc(o)}</button>`;
    }).join("");
    const last = test.i === test.items.length - 1;
    const explain = answered === undefined ? "" :
      `<div class="card explain">${answered === item.a ? esc(t("correct")) : esc(t("wrong")(item.o[item.a]))}<br>${esc(pick(item.e))}</div>
       <button type="button" class="btn main" id="next">${esc(last ? t("finish") : t("next"))}</button>`;
    body.innerHTML = `<div class="meta"><span>${esc(t("qOf")(test.i + 1, test.items.length))}</span><span>${esc(t("sections")[item.s])}</span></div>
      <div class="bar"><span style="width:${Math.round(100 * test.i / test.items.length)}%"></span></div>
      ${passage}<div class="q">${esc(item.q)}</div><div class="opts">${opts}</div>${explain}`;
    body.querySelectorAll(".opts button").forEach((b) => b.onclick = () => { test.answers[test.i] = Number(b.dataset.k); renderTest(body); resize(); });
    const next = body.querySelector("#next");
    if (next) next.onclick = () => { test.i++; renderTest(body); root.scrollTop = 0; resize(); };
  }

  function renderScore(body) {
    const per = {};
    test.items.forEach((it, k) => { per[it.s] = per[it.s] || [0, 0]; per[it.s][1]++; if (test.answers[k] === it.a) per[it.s][0]++; });
    const right = Object.values(per).reduce((s, [r]) => s + r, 0);
    const score = Math.round(100 * right / test.items.length);
    const sections = Object.entries(per).map(([s, [r, n]]) => `<li>${esc(t("sections")[s])}: ${r} / ${n}</li>`).join("");
    const mistakes = test.items.map((it, k) => ({ it, k })).filter(({ it, k }) => test.answers[k] !== it.a)
      .map(({ it }) => `<div class="card"><b>${esc(it.q)}</b><br>✓ ${esc(it.o[it.a])}<br><small>${esc(pick(it.e))}</small></div>`).join("");
    const best = Math.max(score, store.get("examBest", 0)); store.set("examBest", best);
    body.innerHTML = `<div class="card" style="text-align:center">${esc(t("score"))}<div class="big">${score} / 100</div>
        ${esc(score >= 60 ? t("pass") : t("fail"))}</div>
      <h3>${esc(t("bySection"))}</h3><ul>${sections}</ul>
      <h3>${esc(t("review"))}</h3>${mistakes || `<p>${esc(t("noMistakes"))}</p>`}
      <button type="button" class="btn main" id="again">${esc(t("again"))}</button>
      <p><small>${esc(t("practiceOnly"))}</small></p>`;
    body.querySelector("#again").onclick = () => { test = newTest(); test.i = 0; renderTest(body); root.scrollTop = 0; resize(); };
  }

  function renderWriting(body) {
    const saved = store.get("examEssay", "");
    const task = WRITING_TASKS[taskIndex];
    body.innerHTML = `<p>${esc(t("writingIntro"))}</p>
      <div class="card"><b>${esc(t("task"))}:</b> ${esc(task)}<br><button type="button" class="btn" id="another" style="margin-top:6px">${esc(t("another"))}</button></div>
      <textarea id="essay" spellcheck="false" lang="en">${esc(saved)}</textarea>
      <div class="meta"><span id="wc"></span></div>
      <ul>${t("checklist").map((c) => `<li>${esc(c)}</li>`).join("")}</ul>
      <button type="button" class="btn main" id="feedback">${esc(t("getFeedback"))}</button>
      <div id="fb"></div>`;
    const area = body.querySelector("#essay"), wc = body.querySelector("#wc");
    const count = () => (area.value.trim().match(/\S+/g) || []).length;
    const update = () => { wc.textContent = `${t("words")(count())} · ${t("target")}`; store.set("examEssay", area.value); };
    area.oninput = update; update();
    body.querySelector("#another").onclick = () => { taskIndex = (taskIndex + 1) % WRITING_TASKS.length; renderWriting(body); resize(); };
    body.querySelector("#feedback").onclick = async () => {
      const fb = body.querySelector("#fb"), btn = body.querySelector("#feedback");
      if (count() < 50) { fb.innerHTML = `<div class="card note">${esc(t("tooShort"))}</div>`; resize(); return; }
      btn.disabled = true; fb.innerHTML = `<div class="card">${esc(t("thinking"))}</div>`; resize();
      try {
        const data = await requestWritingFeedback(task, area.value.trim());
        fb.innerHTML = `<div class="card note"><span class="tag">${esc(t("feedbackTag"))}</span><div class="feedback">${esc(data.feedback)}</div></div>`;
      } catch (err) {
        fb.innerHTML = `<div class="card note">${esc(t("error")(err.message))}</div>`;
      } finally { btn.disabled = false; resize(); }
    };
  }

  window.ExamPractice = {
    open(el) { root = el; render(); },
    data: { GRAMMAR, VOCAB, PASSAGES, PARAGRAPH },   // used by tests/test_exam.js
    pool: { grammar: GRAMMAR.length, vocab: VOCAB.length, passages: PASSAGES.length, paragraph: PARAGRAPH.length, writing: WRITING_TASKS.length }
  };
})();
