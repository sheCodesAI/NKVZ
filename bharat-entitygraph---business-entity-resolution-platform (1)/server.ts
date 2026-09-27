import express from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { createServer as createViteServer } from 'vite';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

  app.use(express.json());

  // Cache catalog data in memory
  let catalogData: any = null;
  const loadCatalog = () => {
    try {
      const catalogPath = path.resolve(__dirname, 'output', 'catalog_data.json');
      if (fs.existsSync(catalogPath)) {
        catalogData = JSON.parse(fs.readFileSync(catalogPath, 'utf-8'));
      }
    } catch (e) {
      console.error('Error loading catalog data:', e);
    }
  };
  loadCatalog();

  // API Endpoints
  app.get('/api/health', (req, res) => {
    res.json({
      status: 'UP',
      platform: 'Bharat EntityGraph',
      timestamp: new Date().toISOString(),
      models_ready: fs.existsSync(path.resolve(__dirname, 'models', 'bharat_entity_matcher.joblib')),
      submission_ready: fs.existsSync(path.resolve(__dirname, 'output', 'matching_results.tsv')),
    });
  });

  app.get('/api/summary', (req, res) => {
    if (!catalogData) loadCatalog();
    if (!catalogData) {
      return res.status(503).json({ error: 'Catalog data initializing...' });
    }
    res.json({
      system_info: catalogData.system_info,
      data_profile: catalogData.data_profile,
      feature_definitions: catalogData.feature_definitions,
    });
  });

  app.get('/api/entities', (req, res) => {
    if (!catalogData) loadCatalog();
    const { country, status, search, page = '1', limit = '20' } = req.query;
    let entities = catalogData?.canonical_entities || [];

    if (country && country !== 'all') {
      entities = entities.filter((e: any) => e.country.toLowerCase() === String(country).toLowerCase());
    }

    if (status && status !== 'all') {
      if (status === 'singleton') {
        entities = entities.filter((e: any) => e.is_singleton);
      } else if (status === 'matched') {
        entities = entities.filter((e: any) => !e.is_singleton);
      }
    }

    if (search) {
      const q = String(search).toLowerCase();
      entities = entities.filter(
        (e: any) =>
          e.canonical_id.toLowerCase().includes(q) ||
          e.canonical_name.toLowerCase().includes(q) ||
          e.canonical_address.toLowerCase().includes(q)
      );
    }

    const p = Math.max(1, parseInt(String(page)));
    const l = Math.max(1, parseInt(String(limit)));
    const total = entities.length;
    const paginated = entities.slice((p - 1) * l, p * l);

    res.json({
      total,
      page: p,
      limit: l,
      total_pages: Math.ceil(total / l),
      entities: paginated,
    });
  });

  app.get('/api/entities/:id', (req, res) => {
    if (!catalogData) loadCatalog();
    const id = req.params.id;
    const entity = catalogData?.canonical_entities?.find(
      (e: any) => e.canonical_id === id || e.graph_nodes[0]?.id === id
    );

    if (!entity) {
      return res.status(404).json({ error: `Entity ${id} not found in catalog` });
    }

    res.json(entity);
  });

  app.get('/api/runs', (req, res) => {
    if (!catalogData) loadCatalog();
    res.json({
      runs: catalogData?.runs || [],
    });
  });

  app.get('/api/errors', (req, res) => {
    if (!catalogData) loadCatalog();
    res.json({
      error_analysis: catalogData?.error_analysis || [],
    });
  });

  // Live Pairwise Match Evaluation Endpoint
  app.post('/api/match', (req, res) => {
    const { s1_name, s1_addr, s1_country, tgt_name, tgt_addr, tgt_country, tgt_id = 'S2-DEMO' } = req.body;

    if (!s1_name || !tgt_name) {
      return res.status(400).json({ error: 's1_name and tgt_name are required' });
    }

    const pyScript = `
import sys, os, json
sys.path.insert(0, 'code/business_entity_resolution/src')
import normalization as norm
from features import extract_pairwise_features
from model import BharatEntityMatcher
from explainability import generate_pair_explanation
import numpy as np

s1_name = ${JSON.stringify(s1_name)}
s1_addr = ${JSON.stringify(s1_addr || '')}
s1_c = ${JSON.stringify(s1_country || 'India')}

tgt_name = ${JSON.stringify(tgt_name)}
tgt_addr = ${JSON.stringify(tgt_addr || '')}
tgt_c = ${JSON.stringify(tgt_country || s1_country || 'India')}
tgt_id = ${JSON.stringify(tgt_id)}

s1_cn, s1_core, _ = norm.normalize_name(s1_name)
s1_ca, s1_nums, s1_post, _ = norm.normalize_address(s1_addr, s1_c)
s1_tuple = (s1_cn, s1_core, s1_ca, s1_nums, s1_post, s1_c)

tgt_cn, tgt_core, _ = norm.normalize_name(tgt_name)
tgt_ca, tgt_nums, tgt_post, _ = norm.normalize_address(tgt_addr, tgt_c)
tgt_tuple = (tgt_cn, tgt_core, tgt_ca, tgt_nums, tgt_post, tgt_c)

feats = extract_pairwise_features(s1_tuple, tgt_tuple, tgt_id, shared_keys_count=2)

prob = 0.85
if os.path.exists('models/bharat_entity_matcher.joblib'):
    matcher = BharatEntityMatcher.load('models/bharat_entity_matcher.joblib')
    prob = float(matcher.predict_proba(np.array([feats], dtype=np.float32))[0])

explanation = generate_pair_explanation(s1_name, s1_addr, s1_c, tgt_name, tgt_addr, tgt_c, prob, threshold=0.05)

output = {
    'confidence': round(prob, 4),
    'decision': explanation['status'],
    'badge_color': explanation['badge_color'],
    'evidence': explanation['evidence_list'],
    'metrics': {
        'name_jw': explanation['name_jw'],
        'addr_jw': explanation['addr_jw'],
        'token_sort': explanation['token_sort'],
        'country_match': explanation['country_match']
    },
    's1_normalized': {
        'clean_name': s1_cn,
        'core_brand': s1_core,
        'clean_address': s1_ca,
        'postal': s1_post,
        'numbers': s1_nums
    },
    'target_normalized': {
        'clean_name': tgt_cn,
        'core_brand': tgt_core,
        'clean_address': tgt_ca,
        'postal': tgt_post,
        'numbers': tgt_nums
    }
}
print(json.dumps(output))
`;

    const py = spawn('python3', ['-c', pyScript]);
    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (data) => (stdout += data.toString()));
    py.stderr.on('data', (data) => (stderr += data.toString()));

    py.on('close', (code) => {
      if (code !== 0) {
        console.error('Python evaluation error:', stderr);
        return res.status(500).json({ error: 'Failed to evaluate pair with ML model', details: stderr });
      }
      try {
        const result = JSON.parse(stdout.trim());
        res.json(result);
      } catch (e) {
        res.status(500).json({ error: 'Invalid response from model evaluator', raw: stdout });
      }
    });
  });

  // Live Competition Validator Runner Endpoint
  app.post('/api/validate', (req, res) => {
    const validatorCmd = spawn('python3', [
      'utils/validate_submission.py',
      '--matching', 'output/matching_results.tsv',
      '--candidate', 'output/candidate_pairs.tsv',
      '--test-dir', 'dataset/test',
      '--check-ids',
    ]);

    let output = '';
    validatorCmd.stdout.on('data', (d) => (output += d.toString()));
    validatorCmd.stderr.on('data', (d) => (output += d.toString()));

    validatorCmd.on('close', (code) => {
      res.json({
        exit_code: code,
        passed: code === 0,
        output: output.trim(),
        timestamp: new Date().toISOString(),
      });
    });
  });

  // Re-run pipeline and rebuild submission
  app.post('/api/rebuild', (req, res) => {
    const runner = spawn('python3', [
      'code/business_entity_resolution/src/main.py',
      '--test-dir', 'dataset/test',
      '--output-dir', 'output',
    ]);

    let log = '';
    runner.stdout.on('data', (d) => (log += d.toString()));
    runner.stderr.on('data', (d) => (log += d.toString()));

    runner.on('close', (code) => {
      loadCatalog();
      res.json({
        exit_code: code,
        success: code === 0,
        log: log.trim(),
      });
    });
  });

  // Dedicated TSV and Package File Download Endpoints
  app.get('/api/download/:filename', (req, res) => {
    const filename = req.params.filename;
    let filePath = '';

    if (filename === 'matching_results.tsv') {
      filePath = path.resolve(__dirname, 'output', 'matching_results.tsv');
    } else if (filename === 'candidate_pairs.tsv') {
      filePath = path.resolve(__dirname, 'output', 'candidate_pairs.tsv');
    } else if (
      filename === 'submission.zip' ||
      filename === 'bharat_entitygraph_submission.zip'
    ) {
      filePath = path.resolve(__dirname, 'bharat_entitygraph_submission.zip');
    } else if (
      filename === 'all_tsvs.zip' ||
      filename === 'all_challenge_tsvs.zip'
    ) {
      filePath = path.resolve(__dirname, 'output', 'all_challenge_tsvs.zip');
    } else if (
      ['test_source1.tsv', 'test_source2.tsv', 'test_source3.tsv'].includes(filename)
    ) {
      filePath = path.resolve(__dirname, 'dataset', 'test', filename);
    } else if (
      ['train_source1.tsv', 'train_source2.tsv', 'train_source3.tsv', 'train_ground_truth.tsv'].includes(filename)
    ) {
      filePath = path.resolve(__dirname, 'dataset', 'train', filename);
    } else {
      return res.status(404).send('File not found');
    }

    if (fs.existsSync(filePath)) {
      if (filename.endsWith('.tsv')) {
        res.setHeader('Content-Type', 'text/tab-separated-values; charset=utf-8');
      } else if (filename.endsWith('.zip')) {
        res.setHeader('Content-Type', 'application/zip');
      }
      res.download(filePath, filename);
    } else {
      res.status(404).send(`File ${filename} not found on server`);
    }
  });

  // Vite Development Server Middleware
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Bharat EntityGraph Platform listening on port ${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
