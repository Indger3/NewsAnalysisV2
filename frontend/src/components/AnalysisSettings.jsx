import { useState } from 'react'
import {
  Box, Typography, Collapse, Select, MenuItem,
  Slider, FormControl, InputLabel,
} from '@mui/material'

export default function AnalysisSettings({ settings, onChange }) {
  const [open, setOpen] = useState(false)

  return (
    <Box sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
      <Box
        onClick={() => setOpen((o) => !o)}
        sx={{
          px: 3, py: 1.5,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          cursor: 'pointer',
          '&:hover': { bgcolor: 'action.hover' },
        }}
      >
        <Typography sx={{
          fontSize: '0.65rem', fontWeight: 800,
          letterSpacing: 1.8, textTransform: 'uppercase',
          color: 'text.secondary',
        }}>
          Analysis Settings
        </Typography>
        <Typography sx={{ fontSize: '0.7rem', color: 'text.disabled', lineHeight: 1 }}>
          {open ? '▴' : '▾'}
        </Typography>
      </Box>

      <Collapse in={open}>
        <Box sx={{ px: 3, pb: 2.5, display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          <FormControl size="small" fullWidth>
            <InputLabel>NLP Model</InputLabel>
            <Select
              label="NLP Model"
              value={settings.model}
              onChange={(e) => onChange({ ...settings, model: e.target.value })}
            >
              <MenuItem value="ai4bharat/IndicBERTv2-MLM-only">IndicBERT v2</MenuItem>
              <MenuItem value="distilbert-base-uncased">DistilBERT (faster)</MenuItem>
            </Select>
          </FormControl>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: 'block', mb: 0.5 }}
            >
              RE Confidence Threshold: {settings.confidence.toFixed(2)}
            </Typography>
            <Slider
              value={settings.confidence}
              min={0}
              max={1}
              step={0.05}
              onChange={(_, val) => onChange({ ...settings, confidence: val })}
              sx={{ color: 'primary.main', py: 1 }}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.disabled">0.00</Typography>
              <Typography variant="caption" color="text.disabled">1.00</Typography>
            </Box>
          </Box>
        </Box>
      </Collapse>
    </Box>
  )
}
