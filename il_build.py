# Hebrew hub (/il/). Executed from build.py; shares its globals (page, e, ld, faq, tool_link, D, SITE...)
IL=D['il_stack'];IC=IL['checked']
HNAV=[('/il/','בית'),('/il/stack.html','הסטאק'),('/il/playbooks.html','מדריכים'),('/il/cohort.html','מחזור קבוצתי'),('/','English')]
HFOOT=f'''<p><strong>הבהרה משפטית:</strong> האתר נועד למידע כללי בלבד ומסופק "כמות שהוא" (AS IS), ללא אחריות מכל סוג. מחירים, תוכניות ויכולות משתנים לעיתים קרובות ועשויים להיות לא מדויקים או לא מעודכנים (נבדקו לאחרונה ב-{IC}); יש לאמת תמיד מול הספק לפני רכישה. אין באמור ייעוץ משפטי, פיננסי או מקצועי. סימני מסחר שייכים לבעליהם ואינם מהווים המלצה. חלק מהקישורים עשויים להיות קישורי שותפים. הנוסח המחייב הוא הנוסח האנגלי של <a href="/terms.html" lang="en">תנאי השימוש</a> ו<a href="/disclosure.html" lang="en">גילוי נאות לשותפים</a>.</p>
<p class="mut">הערה: התרגום לעברית טרם עבר בדיקה של דובר/ת עברית ועורך/ת דין. · <a href="/privacy.html">פרטיות</a> · <a href="/corrections.html">תיקונים והסרות</a> · © 2026 [Legal entity name]</p>'''
HALT=lambda p:{'he':SITE+'/il/'+p,'en':SITE+'/','x-default':SITE+'/'}
def hpage(p,title,desc,body,schema=(),hero=''):
  sch=[dict(x,inLanguage='he') for x in schema]
  page('il/'+p,title,desc,body,sch,hero,lang='he',nav=HNAV,foot=HFOOT,alts=HALT('' if p=='index.html' else p))
def hfaq(qs): return '<h2>שאלות נפוצות</h2>'+''.join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q,a in qs)
items=IL['items'];total=sum(i['price'] or 0 for i in items)
# ---- hub
hero=f'''<section class="hero"><div class="wrap"><span class="pill">למייסדים ישראלים בשלב Pre-seed ומוקדם יותר</span><h1>השיחות הראשונות שלך <span class="grad">בארה"ב</span></h1>
<p>איך מגיעים ל-20 שיחות המכירה הראשונות בשוק האמריקאי (או בכל שוק אחר שתבחרו) עם תקציב של כמה עשרות דולרים בחודש, בלי צוות מכירות ובלי משקיעים.</p>
<p><a class="btn" href="/il/stack.html">הסטאק ב-${total} לחודש</a> <a class="btn ghost" href="/il/playbooks.html">למדריכים</a></p></div></section>'''
Q=[('כמה עולה להתחיל למכור לארה"ב מישראל?',f'בערך ${total} לחודש לפי מחירי המחירון שפורסמו בעמודי הספקים ({IC}), לא כולל דומיין, מע"מ וכלי אוטומציה ללינקדאין. זו הערכה בלבד; יש לאמת מול כל ספק.'),
('צריך חברה אמריקאית כדי להתחיל לדבר עם לקוחות?','לשיחות הראשונות בדרך כלל לא. מספר טלפון אמריקאי, תיבת מייל על דומיין משלכם וקישור לתיאום פגישות מספיקים כדי להתחיל. לגבי התאגדות, מיסים וחוזים, התייעצו עם רואה חשבון ועורך דין.'),
('באיזה שוק להתחיל?','בחרו שוק אחד מצומצם (Beachhead): פלח, תפקיד וגיאוגרפיה שבהם הבעיה הכי כואבת ויש לכם גישה לאנשים. אפשר להתחיל גם מחוץ לארה"ב, וההיגיון נשאר זהה.')]
cards=''.join(f'<a class="card" href="{h}"><h3>{t}</h3><p class="mut">{d}</p></a>' for h,t,d in [('/il/stack.html','הסטאק הזול','כלי אחד לכל משימה, בלי כפילויות, עם מחירים ומקורות.'),('/il/playbooks.html','מדריכים ותבניות','20 השיחות הראשונות, תבניות באנגלית למייל ולינקדאין, וטון אמריקאי.'),('/il/cohort.html','מחזור קבוצתי','גרסה קבוצתית ומשתלמת של ספרינט ה-GTM. רשימת המתנה.')])
hpage('index.html','השיחות הראשונות שלך בארה"ב | Profitable Agent Stack','מדריך למייסדים ישראלים בשלב מוקדם: איך להגיע לשיחות מכירה ראשונות בארה"ב עם סטאק של עד $100 לחודש, תבניות באנגלית ומחזור קבוצתי.',
f'<h2>{e(Q[0][0])}</h2><p class="answer">{e(Q[0][1])}</p><div class="grid">{cards}</div>{hfaq(Q)}',[{"@context":"https://schema.org","@type":"WebPage","name":'השיחות הראשונות שלך בארה"ב',"url":SITE+'/il/'},faq(Q)],hero)
# ---- stack
def lnk(i):
  h,rel,aff=tool_link(i);logo=i.get('logo')
  img=f'<img class="logo-img" src="{logo}" alt="הלוגו של {e(i["tool"])}" width="32" height="32" loading="lazy">' if logo else ''
  return f'<a href="{e(h)}" target="_blank" rel="{rel}" class="row" style="color:inherit"><bdi>{e(i["tool"])}</bdi></a>'+(' <span class="badge c">שותפים</span>' if aff else ''),img
rows=''
for i in items:
  a,img=lnk(i);pr='לא אומת' if i['status']=='unverified' else ('$0' if i['price']==0 else f'${i["price"]}')
  rows+=f'<tr><td>{e(i["job"])}</td><td><div class="row">{img}{a}</div><span class="mut">{e(i["tier"])}</span></td><td><b>{pr}</b><br><span class="mut">{e(i["price_note"])}</span></td><td class="mut">{e(i["why"])}</td><td><a href="{i["source"]}" target="_blank" rel="nofollow noopener">מקור</a></td></tr>'
SQ=[('מה הסטאק הכי זול למכירה לארה"ב מישראל?',f'Quo למספר אמריקאי, Google Workspace לתיבת מייל, Hunter לאיתור מיילים, Smartlead לרצפים (כולל חימום), Cal.com לתיאום, HubSpot CRM ו-PostHog. סך הכול כ-${total} לחודש, לא כולל דומיין.'),
('למה אין כאן כלי חימום נפרד?','כי עמוד התמחור של Smartlead מציין חימום ללא הגבלה, כך שכלי נוסף היה כפילות.'),('למה לינקדאין ידני?','ב-20 השיחות הראשונות הודעה אישית שנכתבה ידנית מקבלת בדרך כלל יותר תגובות. אוטומציה (Waalaxy, €19) שווה שקילה רק כשהנפח עולה.')]
hpage('stack.html',f'סטאק ב-${total} לחודש למכירה לארה"ב מישראל | Profitable Agent Stack','סטאק כלים זול למייסדים ישראלים שמוכרים לארה"ב: כלי אחד לכל משימה, מחירים מאומתים מעמודי הספקים ונימוק לכל בחירה.',
f'''<h1>{e(SQ[0][0])}</h1><p class="answer">{e(SQ[0][1])}</p>
<div style="overflow-x:auto"><table><thead><tr><th>משימה</th><th>כלי</th><th>מחיר לחודש</th><th>למה דווקא הוא</th><th>מקור</th></tr></thead><tbody>{rows}<tr><th colspan="2">סה"כ משוער</th><th colspan="3">${total} לחודש + דומיין (מחיר לא אומת)</th></tr></tbody></table></div>
<p class="mut">חישוב: $19 + $7 + $39 = ${total}. הנחות: מייסד/ת אחד/ת, משתמש אחד בכל כלי, חיוב חודשי, נפח של עד כמה מאות מיילים בחודש. המחירים נבדקו ב-{IC} בעמודי הספקים, לא כוללים מע"מ, ועשויים להשתנות; יש לאמת מול הספק. כלי אחד לכל משימה: חלק מהמשימות (למשל חימום) מכוסות בכוונה על ידי כלי שכבר נמצא בסטאק.</p>
<p class="mut">לוגואים וסימני מסחר שייכים לבעליהם ומשמשים לזיהוי המוצרים בלבד, ואינם מעידים על שותפות או המלצה. בעלי סימנים יכולים לבקש הסרה דרך <a href="/corrections.html">עמוד התיקונים</a>.</p>{hfaq(SQ)}''',
[{"@context":"https://schema.org","@type":"ItemList","name":'סטאק למכירה לארה"ב מישראל',"itemListElement":[{"@type":"ListItem","position":n+1,"item":dict({"@type":"SoftwareApplication","name":i['tool'],"url":i['source'],"applicationCategory":"BusinessApplication"},**({"offers":{"@type":"Offer","price":i['price'],"priceCurrency":"USD","url":i['source']}} if i['status']=='published' and i['price'] is not None else {}))} for n,i in enumerate(items)]},faq(SQ)])
# ---- playbooks
T=lambda x:f'<pre class="ltr" lang="en" dir="ltr">{e(x)}</pre>'
PB=[('איך מגיעים ל-20 השיחות הראשונות?','<ol><li>כתבו בשורה אחת למי אתם עוזרים ובאיזו בעיה (באנגלית).</li><li>בנו רשימה של 100 אנשים בפלח אחד: אותו תפקיד, אותו סוג חברה.</li><li>שלחו 10–15 פניות אישיות ביום, במייל ובלינקדאין.</li><li>בקשו שיחה של 15–20 דקות כדי ללמוד, לא כדי למכור.</li><li>תעדו כל שיחה ב-CRM ושפרו את המסר כל שבוע.</li></ol><p>היעד: 20 שיחות בתוך 30 יום. זו לא הבטחה, אלא קצב עבודה.</p>'),
('תבנית למייל קר (באנגלית)',T("Subject: quick question about {{pain}} at {{company}}\n\nHi {{first_name}},\n\nI'm {{your_name}}, founder of {{product}}. We help {{role}}s at {{company_type}} {{outcome}} without {{common_cost}}.\n\nI'm not selling anything yet. I'm talking to 20 {{role}}s to learn how you handle {{pain}} today.\n\nWould you be open to a 15-minute call next week? Here's my calendar: {{cal_link}}\n\nThanks,\n{{your_name}}")),
('תבנית לבקשת חיבור והודעת המשך בלינקדאין (באנגלית)',T("Connection note:\nHi {{first_name}}, I'm building {{product}} for {{role}}s dealing with {{pain}}. Would love to connect and learn from your experience.\n\nFollow-up after connecting:\nThanks for connecting, {{first_name}}! Quick question: how does your team handle {{pain}} today? If it's useful, I'd value 15 minutes of your perspective. No pitch.")),
('איך להתאים את הישירות הישראלית לטון אמריקאי?','<ul><li>פתחו בתודה או בהקשר לפני שאתם עוברים לעניין.</li><li>ריככו ביקורת: במקום <span class="ltr" lang="en">"That\'s wrong"</span> כתבו <span class="ltr" lang="en">"I see it a bit differently"</span>.</li><li>הציעו במקום לדרוש: <span class="ltr" lang="en">"Would you be open to…"</span>.</li><li>קצר ונקי: 3–5 משפטים במייל, בלי ז\'רגון.</li><li>תמיד מסיימים עם צעד הבא ברור (קישור ליומן).</li></ul>'),
('איך משתמשים ברשת התפוצות ובמשקיעים?','<ul><li>מפו ישראלים שעובדים בחברות היעד שלכם בארה"ב (חיפוש בלינקדאין לפי חברה ו"Israel").</li><li>בקשו מהם תובנה, לא הכרות. ההכרות מגיעה בדרך כלל לבד.</li><li>שאלו משקיעים, אנג\'לים ומנטורים: "מי שלושת האנשים שהכי כדאי לי לדבר איתם?"</li><li>היעזרו בקהילות ואירועים של מייסדים ישראלים בארה"ב, ותמיד החזירו טובה.</li></ul>'),
('איך בוחרים שוק ראש גשר (Beachhead)?','<ul><li>פלח אחד שבו הבעיה הכי דחופה ומישהו כבר משלם כדי לפתור אותה.</li><li>תפקיד אחד שמחליט על הרכישה.</li><li>אזור או שוק אחד שיש לכם בו גישה (קשרים, שפה, אזור זמן).</li><li>אם השיחות לא מתקדמות אחרי 20–30 ניסיונות, שנו פלח אחד בכל פעם.</li></ul>'),
('איך עובדים עם הפרשי השעות?','<ul><li>החוף המזרחי מאחורי ישראל ב-7 שעות ברוב השנה, והמערבי ב-10. בכמה שבועות באביב ובסתיו ההפרש משתנה, כי שעון הקיץ מתחלף בתאריכים שונים.</li><li>פתחו ביומן חלונות של 16:00–20:00 שעון ישראל לחוף המזרחי, ו-19:00–22:00 למערבי.</li><li>תזמנו שליחת מיילים לבוקר אצל הנמען (8:00–10:00 בשעון שלו).</li><li>השתמשו בקישור תיאום שמציג לקונה את השעות באזור הזמן שלו.</li></ul>')]
PQ=[('איך מגיעים ל-20 שיחות מכירה ראשונות בארה"ב?','בוחרים פלח אחד, בונים רשימה של 100 אנשים, שולחים 10–15 פניות אישיות ביום במייל ובלינקדאין, מבקשים שיחת למידה של 15 דקות, ומשפרים את המסר כל שבוע.'),('באיזו שעה כדאי לקבוע שיחות עם לקוחות בארה"ב?','לחוף המזרחי בדרך כלל בין 16:00 ל-20:00 שעון ישראל, ולמערבי בין 19:00 ל-22:00. בשבועות שבהם שעון הקיץ מתחלף, בדקו שוב את ההפרש.')]
hpage('playbooks.html','מדריכים ותבניות למכירה לארה"ב | Profitable Agent Stack','מדריכים בעברית ותבניות באנגלית למייסדים ישראלים: 20 שיחות ראשונות, מייל קר, לינקדאין, טון אמריקאי, רשתות קשרים ואזורי זמן.',
f'<h1>{e(PQ[0][0])}</h1><p class="answer">{e(PQ[0][1])}</p>'+''.join(f'<section class="card" style="margin:16px 0"><h2 style="margin-top:0">{h}</h2>{b}</section>' for h,b in PB)+hfaq(PQ[1:]),[faq(PQ)])
# ---- cohort
CQ=[('מה זה המחזור הקבוצתי?','גרסה קבוצתית ומשתלמת של ספרינט ה-GTM: קבוצה קטנה של מייסדים ישראלים שבונים יחד סטאק, רשימה ומסרים, ויוצאים ל-20 השיחות הראשונות. המחיר טרם נקבע.'),('כמה זה עולה?','המחיר טרם נקבע. הצטרפו לרשימת ההמתנה ונעדכן.')]
hpage('cohort.html','מחזור קבוצתי: השיחות הראשונות בארה"ב | Profitable Agent Stack','מחזור קבוצתי למייסדים ישראלים בשלב מוקדם, להגעה לשיחות מכירה ראשונות בארה"ב. המחיר טרם נקבע. רשימת המתנה.',
f'''<h1>{e(CQ[0][0])}</h1><p class="answer">{e(CQ[0][1])}</p>
<div class="grid"><div class="card"><h3>מה בונים</h3><p>מסר באנגלית, רשימת 100 לקוחות פוטנציאליים, הסטאק הזול ותבניות פנייה.</p></div><div class="card"><h3>איך זה עובד</h3><p>מפגשים קבוצתיים, ליווי של CRO פרקטי ועבודה שמבוצעת בעזרת סוכני AI.</p></div><div class="card feat"><h3>מחיר</h3><p class="score" style="color:#fff;-webkit-text-fill-color:#fff">טרם נקבע</p><p>רשימת המתנה</p></div></div>
<form class="card" style="margin-top:20px" onsubmit="event.preventDefault();this.innerHTML='<p role=status>תודה! הטופס עדיין לא פעיל, ולכן לא נשמר או נשלח דבר.</p>'"><h2 style="margin-top:0">הצטרפות לרשימת ההמתנה</h2>
<p><label>שם<br><input required></label></p><p><label>אימייל<br><input type="email" required dir="ltr"></label></p><p><label>שוק יעד<br><input placeholder='ארה"ב / אחר'></label></p><p><label>מה אתם מוכרים, במשפט אחד<br><textarea rows="3" style="width:100%"></textarea></label></p><button class="btn">שליחה</button><p class="mut">טופס לדוגמה בלבד: שום מידע לא נאסף או נשלח כרגע.</p></form>
<p class="mut">אין התחייבות לתוצאות. התוכנית בהכנה ואינה פתוחה עדיין להרשמה.</p>{hfaq(CQ[1:])}''',[faq(CQ)])
