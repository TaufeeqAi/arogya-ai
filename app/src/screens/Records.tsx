import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Linking, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { get, url } from '../api';
import { GenUI } from '../components/GenUI';
import { Btn, Card, Pill, SectionTitle, TrustBadge } from '../components/ui';
import { useStore } from '../store';
import { C, font } from '../theme';

const TYPE: Record<string, [string, string]> = {
  lab_report: ['🧪', 'Lab report'],
  prescription: ['💊', 'Prescription'],
  consultation_note: ['🩺', 'Consultation'],
};

export default function Records() {
  const { dataVersion, approvals, decide, send, upload, lastExtraction, activity } = useStore();
  const [uploading, setUploading] = useState('');
  const pick = () => {
    if (Platform.OS !== 'web') return;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/pdf,image/*';
    input.onchange = async () => {
      const f = input.files?.[0];
      if (!f) return;
      setUploading(`Uploading ${f.name}…`);
      try {
        await upload(f, f.name);
        setUploading('AI is reading your document…');
      } catch (e: any) {
        setUploading(`Upload failed: ${e.message}`);
      }
    };
    input.click();
  };
  useEffect(() => {
    if (lastExtraction) setUploading('');
  }, [lastExtraction]);
  const [docs, setDocs] = useState<any[]>([]);
  const [cmp, setCmp] = useState<any>(null);
  const [open, setOpen] = useState<any>(null);
  useEffect(() => {
    get('/api/documents').then(setDocs).catch(() => {});
    get('/api/comparison').then(setCmp).catch(() => {});
  }, [dataVersion]);
  const ctx = { say: send, decide, approvals };

  if (open) {
    return (
      <ScrollView contentContainerStyle={s.page}>
        <Pressable onPress={() => setOpen(null)}>
          <Text style={{ color: C.primary, fontWeight: '700', marginBottom: 10 }}>‹ Health Locker</Text>
        </Pressable>
        {open.observations?.length ? (
          <GenUI
            ctx={ctx}
            item={{ id: open.id, component: 'lab_summary', version: 1, props: { document: { id: open.id, title: open.title, date: open.issued_on, source_name: open.source_name, trust_label: open.trust_label }, observations: open.observations } }}
          />
        ) : (
          <Card>
            <Text style={font.h3}>{open.title}</Text>
            <Text style={[font.small, { marginBottom: 8 }]}>{open.source_name} · {open.issued_on}</Text>
            {open.text.split('\n').map((l: string, i: number) => (
              <Text key={i} style={[font.body, { marginBottom: 4 }]}>{l}</Text>
            ))}
          </Card>
        )}
        <Btn kind="soft" title="Open original document (PDF)" onPress={() => Linking.openURL(url(open.file_url))} />
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={s.page}>
      <Text style={font.h1}>Health Locker</Text>
      <Text style={[font.small, { marginBottom: 14 }]}>Every value links back to its original document.</Text>
      <Btn title="⬆  Upload a report or prescription" onPress={pick} />
      {uploading ? (
        <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center', marginTop: 10 }}>
          {uploading.startsWith('Upload failed') ? null : <ActivityIndicator color={C.primary} />}
          <Text style={font.small}>{uploading}</Text>
        </View>
      ) : null}
      {lastExtraction && <View style={{ marginTop: 12 }}><GenUI ctx={ctx} item={lastExtraction} /></View>}
      <View style={{ height: 12 }} />
      {cmp && <GenUI ctx={ctx} item={{ id: 'cmp', component: 'comparison_chart', version: 1, props: cmp }} />}
      <SectionTitle right={<Pill text={`${docs.length} documents`} />}>Documents</SectionTitle>
      {docs.map((d) => (
        <Pressable key={d.id} onPress={() => get(`/api/documents/${d.id}`).then(setOpen)}>
          <Card style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <Text style={{ fontSize: 26 }}>{TYPE[d.doc_type]?.[0] || '📄'}</Text>
            <View style={{ flex: 1, gap: 3 }}>
              <Text style={font.h3}>{d.title}</Text>
              {d.status !== 'processed' ? <Pill text={d.status === 'extracting' ? 'AI extracting…' : d.status === 'needs_review' ? 'Needs your review' : d.status} tone="warn" /> : null}
              <Text style={font.small}>{TYPE[d.doc_type]?.[1]} · {d.source_name} · {d.source_type === 'provider_import' ? 'Synced from provider' : 'Uploaded by you'}</Text>
              <View style={{ flexDirection: 'row', gap: 6 }}>
                <TrustBadge label={d.trust_label} />
                <Pill text={`sha256 ${d.sha256}…`} />
              </View>
            </View>
            <Text style={{ color: C.muted, fontSize: 20 }}>›</Text>
          </Card>
        </Pressable>
      ))}
    </ScrollView>
  );
}

const s = StyleSheet.create({ page: { padding: 16, paddingBottom: 40, maxWidth: 720, width: '100%', alignSelf: 'center' } });
