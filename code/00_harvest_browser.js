// Step 0 (run in a web browser, not in Python). Counts of Hansard contributions that mention each place.
//
// Run in the developer console of a tab open on https://hansard-api.parliament.uk/ (the API allows same-origin
// requests from there; members-api.parliament.uk allows cross-origin requests). No Hansard text is downloaded:
// the Hansard API's timeline-stats endpoint returns, for a search term, the number of matching contributions per year.
// The page then saves one gzipped JSON bundle (hansard_places_bundle.json.gz), read by step 3.
//
// TERMS is the list in work/terms.json (written by 01_places.py) plus a few nations, regions and London boroughs.
// Every search is a quoted phrase, in the House of Commons, contribution type "Spoken".
//   places:  "<name>" and "in <name>", 1900-01-01 to 2026-10-28, counts per year
//   members: every Commons member who sat at any time from 5 May 2005 to 29 October 2026 (Members API search) and
//            their seat history (Members API History)
//   cons:    for every seat name held by those members: "<seat>" and "Member for <seat>", 2005-01-01 onwards
//   spans:   for each member and seat: "<seat>" spoken by that member (queryParameters.memberId) while holding it

const sleep = ms => new Promise(r => setTimeout(r, ms));
const HV = { places: {}, cons: {}, memberships: [], members: {}, failed: [] };
async function getTS(term, start, end, memberId) {
  const u = 'https://hansard-api.parliament.uk/timeline-stats.json?queryParameters.searchTerm=' + encodeURIComponent(term) +
    '&queryParameters.house=Commons&queryParameters.timelineGroupingSize=Year&queryParameters.startDate=' + start +
    '&queryParameters.endDate=' + (end || '2026-10-28') + '&contributionType=Spoken' + (memberId ? '&queryParameters.memberId=' + memberId : '');
  for (let k = 0; k < 3; k++) {
    const ac = new AbortController(); const to = setTimeout(() => ac.abort(), 30000);
    try {
      const r = await fetch(u, { signal: ac.signal }); clearTimeout(to);
      if (r.status == 200) { const j = await r.json(); if (j && j.Results) { const o = {}; for (const x of j.Results) if (x.Count) o[x.GroupingDate.slice(0, 4)] = x.Count; return o; } }
      else if (r.status == 429 || r.status >= 500) await sleep(3000 * (k + 1)); else break;
    } catch (e) { clearTimeout(to); await sleep(2000); }
  }
  HV.failed.push(term + '|' + (memberId || '')); return null;   // very common words (e.g. "Deal") time out: recorded as null
}
async function pool(items, fn, conc = 3) { let i = 0; const w = async () => { while (i < items.length) { const it = items[i++]; await fn(it); await sleep(60); } }; await Promise.all(Array.from({ length: conc }, w)); }
async function mget(u) { for (let k = 0; k < 4; k++) { try { const r = await fetch(u); if (r.status == 200) return await r.json(); await sleep(2000 * (k + 1)); } catch (e) { await sleep(2000); } } return null; }

async function run(TERMS) {
  await pool(TERMS, async t => { HV.places[t] = { all: await getTS('"' + t + '"', '1900-01-01'), in: await getTS('"in ' + t + '"', '1900-01-01') }; });
  const B = 'https://members-api.parliament.uk/api/Members/Search?House=1&MembershipInDateRange.WasMemberOnOrAfter=2005-05-05&MembershipInDateRange.WasMemberOnOrBefore=2026-10-29&MembershipInDateRange.WasMemberOfHouse=1&take=20&skip=';
  let skip = 0, tot = 1e9;
  while (skip < tot) { const j = await mget(B + skip); if (j) { tot = j.totalResults; for (const it of j.items) { const v = it.value; HV.members[v.id] = { name: v.nameDisplayAs, listAs: v.nameListAs }; } } skip += 20; }
  const ids = Object.keys(HV.members);
  for (let i = 0; i < ids.length; i += 20) {
    const j = await mget('https://members-api.parliament.uk/api/Members/History?ids=' + ids.slice(i, i + 20).join('&ids='));
    for (const it of j || []) { const v = it.value; for (const m of v.houseMembershipHistory) { if (m.house != 1 || (m.membershipEndDate && m.membershipEndDate < '2005-05-05')) continue;
      HV.memberships.push({ id: v.id, cons: m.membershipFrom, consId: m.membershipFromId, start: m.membershipStartDate.slice(0, 10), end: m.membershipEndDate ? m.membershipEndDate.slice(0, 10) : null }); } }
  }
  const sp = {};
  for (const m of HV.memberships) { const k = m.id + '|' + m.cons, s = m.start < '2005-01-01' ? '2005-01-01' : m.start, e = m.end || '2026-10-28';
    if (!sp[k]) sp[k] = { id: m.id, cons: m.cons, start: s, end: e }; else { if (s < sp[k].start) sp[k].start = s; if (e > sp[k].end) sp[k].end = e; } }
  HV.spans = Object.values(sp);
  const names = [...new Set(HV.spans.map(s => s.cons))];
  await pool(names, async n => { HV.cons[n] = { all: await getTS('"' + n + '"', '2005-01-01'), mf: await getTS('"Member for ' + n + '"', '2005-01-01') }; });
  await pool(HV.spans, async s => { s.own = await getTS('"' + s.cons + '"', s.start, s.end, s.id); });
  // save: gzip the bundle and offer it as a download
  const obj = { source: 'UK Parliament Hansard API (hansard-api.parliament.uk, timeline-stats, Commons, Spoken) and Members API (members-api.parliament.uk)',
    licence: 'Open Parliament Licence v3.0', retrieved: new Date().toISOString().slice(0, 10), ...HV };
  const blob = await new Response(new Blob([JSON.stringify(obj)]).stream().pipeThrough(new CompressionStream('gzip'))).blob();
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'hansard_places_bundle.json.gz'; a.textContent = 'Download'; document.body.prepend(a);
}
