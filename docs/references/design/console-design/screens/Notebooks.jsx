/* Notebooks — research journal with linked claims. */

const NotebooksScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("nb_01");
  const [q, setQ] = useState("");
  const [drawer, setDrawer] = useState(null);
  const selected = FIX_NOTEBOOKS.find(n => n.id === selectedId);
  const filtered = q ? FIX_NOTEBOOKS.filter(n => n.title.toLowerCase().includes(q.toLowerCase()) || n.excerpt.toLowerCase().includes(q.toLowerCase())) : FIX_NOTEBOOKS;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("nb.title")} subtitle={t("nb.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("nb.search")} width={220}/>
        <button className="btn primary sm" onClick={() => setDrawer({})}><Icon name="plus" size={11}/> {t("nb.new")}</button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="book" size={12}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("nb.notes")}</span>
            <span className="chip">{filtered.length}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {filtered.map(n => {
              const active = n.id === selectedId;
              return (
                <div key={n.id} onClick={() => setSelectedId(n.id)} style={{
                  padding: "12px 14px", cursor: "pointer",
                  background: active ? "var(--bg-hover)" : "transparent",
                  borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
                  borderBottom: "1px solid var(--border-subtle)",
                }}>
                  <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 4, lineHeight: 1.4 }}>{n.title}</div>
                  <div style={{ fontSize: 10, color: "var(--fg-muted)", lineHeight: 1.5, overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{n.excerpt}</div>
                  <div style={{ display: "flex", gap: 8, marginTop: 6, fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                    <span>{n.word_count}w</span>
                    <span>·</span>
                    <span>{new Date(n.updated_at).toISOString().slice(5,10)}</span>
                    {n.linked_claims.length > 0 && <span style={{ color: "var(--accent)" }}>· {n.linked_claims.length}📎</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {selected && (
          <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>
                    {new Date(selected.updated_at).toISOString().replace("T"," ").slice(0,16)} · {selected.author}
                  </div>
                  <div style={{ fontSize: 17, fontWeight: 500, letterSpacing: "-0.005em" }}>{selected.title}</div>
                </div>
                <button className="btn sm"><Icon name="copy" size={10}/> {t("act.edit")}</button>
              </div>
            </div>

            <div style={{ flex: 1, overflow: "auto", padding: "24px 32px", display: "flex", flexDirection: "column", gap: 14 }}>
              <p style={{ fontSize: 13, lineHeight: 1.75, color: "var(--fg-muted)", margin: 0 }}>
                {selected.excerpt}
              </p>
              <p style={{ fontSize: 13, lineHeight: 1.75, color: "var(--fg-muted)", margin: 0 }}>
                The dataset in question is <span className="mono" style={{ color: "var(--accent)" }}>ds_medqa_multi_v3</span>, which we sampled at n=1200 per language. Below is a summary of the pattern I observed while browsing the failure cases:
              </p>
              <ul style={{ fontSize: 13, lineHeight: 1.75, color: "var(--fg-muted)", margin: 0, paddingLeft: 20 }}>
                <li>Generic-name substitution: "amoxicilina" → "amoxicillin" was accepted but "0.5g" → "500mg" was frequently converted incorrectly.</li>
                <li>Dosage-unit confusion: mg vs g vs mL — most failures are unit-conversion in Spanish and Chinese.</li>
                <li>Frequency prepositions: "cada 8 horas" and "q8h" are not being unified in the eval pipeline.</li>
              </ul>
              <p style={{ fontSize: 13, lineHeight: 1.75, color: "var(--fg-muted)", margin: 0 }}>
                Next step: instrument the eval harness to bucket errors by category and re-run the Spanish subset with a stricter normalization step. Filed as <span className="mono" style={{ color: "var(--accent)" }}>exp_q_01K5FZ8P2M3N</span>.
              </p>

              {selected.linked_claims.length > 0 && (
                <div style={{ marginTop: 20, padding: 14, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8 }}>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 8 }}>{t("nb.linkedClaims")} {selected.linked_claims.length}</div>
                  {selected.linked_claims.map(cid => {
                    const c = FIX_CLAIMS.find(x => x.id === cid);
                    if (!c) return null;
                    return (
                      <div key={cid} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "6px 0", borderTop: "1px solid var(--border-subtle)" }}>
                        <ClaimStatusBadge status={c.status}/>
                        <div style={{ flex: 1, fontSize: 11, color: "var(--fg)" }}>{c.statement}</div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <Drawer open={!!drawer} onClose={() => setDrawer(null)} title={t("nb.new")} subtitle={t("nb.newSub")} width={480}
        footer={<>
          <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
          <button className="btn primary" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}><Icon name="check" size={11}/> {t("act.save")}</button>
        </>}>
        <FormRow label={t("lbl.title")} required><TextInput placeholder={t("nb.form.titlePh")}/></FormRow>
        <FormRow label={t("lbl.body")} hint={t("proj.form.notesHint")}><TextArea rows={8} placeholder={t("nb.form.bodyPh")}/></FormRow>
        <FormRow label={t("nb.form.link")}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 160, overflow: "auto", padding: 4, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 6 }}>
            {FIX_CLAIMS.slice(0, 4).map(c => (
              <label key={c.id} style={{ display: "flex", gap: 8, padding: "4px 6px", cursor: "pointer", fontSize: 11 }}>
                <input type="checkbox" style={{ accentColor: "var(--accent)" }}/>
                <ClaimStatusBadge status={c.status}/>
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.statement.slice(0, 60)}…</span>
              </label>
            ))}
          </div>
        </FormRow>
      </Drawer>
    </div>
  );
};

Object.assign(window, { NotebooksScreen });
